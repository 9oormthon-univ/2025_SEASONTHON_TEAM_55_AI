import json
import os
from pathlib import Path
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from .models import RiskLevel

class PortfolioService:
    def __init__(self, openai_api_key: str = None):
        if not openai_api_key:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY 환경변수 또는 API 키가 필요합니다")

        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=openai_api_key
        )

        # 데이터 파일 경로 설정
        dataset_path = Path(__file__).parent.parent.parent / "recommend" / "financial_portfolio_dataset.json"

        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"필수 데이터 파일이 없습니다: {dataset_path}")

        # 데이터 분리
        self.savings = self.data.get("savings", [])
        self.deposits = self.data.get("deposits", [])
        bonds_data = self.data.get("bonds", [])
        # bonds가 리스트인 경우와 딕셔너리인 경우 모두 처리
        if isinstance(bonds_data, list):
            self.bonds = bonds_data
        else:
            self.bonds = bonds_data.get("sortByInterest", []) + bonds_data.get("sortByMaturity", [])
        self.etfs = self.data.get("etfs", [])

    def get_gpt_allocation(self, risk_level: RiskLevel, target_amount: int, period: int):
        """GPT를 사용해서 맞춤형 자산 배분 추천"""

        system_prompt = """
당신은 전문 금융 자산배분 어드바이저입니다.
사용자의 위험성향, 투자금액, 투자기간을 분석해서 최적의 포트폴리오 배분을 추천해주세요.

배분 가능한 자산군:
- deposit (예금): 안전하지만 수익률 낮음 (2-3%)
- saving (적금): 예금보다 약간 높은 수익률 (3-4%)
- bond (채권): 중간 수익률과 안정성 (4-5%)
- etf (ETF): 높은 수익률 가능하지만 변동성 있음 (6-10%)

규칙:
1. 4개 자산군 모두 포함해야 함 (최소 5% 이상)
2. 전체 비율 합계는 반드시 100%
3. 위험성향에 따른 배분 가이드라인:
   - 안정형: 예금+적금 위주 (60-80%)
   - 안정추구형: 예금+적금+채권 균형 (각각 20-40%)
   - 위험중립형: 4개 자산군 고른 배분
   - 적극투자형: ETF 비중 높임 (40-60%)
   - 공격투자형: ETF 최대 비중 (60-80%)

응답 형식 (JSON만 출력):
{
  "deposit": 숫자,
  "saving": 숫자,
  "bond": 숫자,
  "etf": 숫자,
  "reasoning": "배분 근거 설명"
}
"""

        user_prompt = f"""
사용자 정보:
- 위험성향: {risk_level.value}
- 투자금액: {target_amount:,}원
- 투자기간: {period}개월

이 사용자에게 최적의 포트폴리오 자산배분을 추천해주세요.
투자금액과 기간을 고려한 맞춤형 배분을 제시해주세요.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            # JSON 블록 찾기
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("GPT 응답에서 JSON을 찾을 수 없습니다")

            json_str = response_text[start_idx:end_idx]
            allocation_data = json.loads(json_str)

            # 비율 검증 및 정규화
            required_keys = ['deposit', 'saving', 'bond', 'etf']
            for key in required_keys:
                if key not in allocation_data:
                    allocation_data[key] = 10

            total = sum(allocation_data[key] for key in required_keys)
            if abs(total - 100) > 1:
                for key in required_keys:
                    allocation_data[key] = round(allocation_data[key] * 100 / total)

            final_allocation = {key: allocation_data[key] for key in required_keys}
            reasoning = allocation_data.get('reasoning', 'GPT 기반 맞춤 추천')

            return final_allocation, reasoning

        except Exception as e:
            fallback = self.get_fallback_allocation(risk_level)
            return fallback, f"GPT 오류로 인한 기본 배분 적용 (오류: {str(e)})"

    def get_fallback_allocation(self, risk_level: RiskLevel):
        """GPT 실패 시 사용할 기본 배분"""
        mapping = {
            RiskLevel.STABLE: {"deposit": 40, "saving": 30, "bond": 20, "etf": 10},
            RiskLevel.STABILITY_SEEKING: {"deposit": 30, "saving": 25, "bond": 25, "etf": 20},
            RiskLevel.RISK_NEUTRAL: {"deposit": 20, "saving": 20, "bond": 30, "etf": 30},
            RiskLevel.ACTIVE_INVESTMENT: {"deposit": 10, "saving": 15, "bond": 25, "etf": 50},
            RiskLevel.AGGRESSIVE_INVESTMENT: {"deposit": 5, "saving": 10, "bond": 15, "etf": 70},
        }
        return mapping.get(risk_level, {"deposit": 25, "saving": 25, "bond": 25, "etf": 25})

    def filter_products(self, product_type: str, period: int):
        """기간에 맞는 상품 필터링 후 금리순 정렬"""
        if product_type == "deposit":
            products = sorted(self.deposits, key=lambda x: x.get("bestRate", 0), reverse=True)
            return [p for p in products if p.get("bestTerm", 0) <= period]
        elif product_type == "saving":
            products = sorted(self.savings, key=lambda x: x.get("bestRate", 0), reverse=True)
            return [p for p in products if p.get("bestTerm", 0) <= period]
        elif product_type == "bond":
            today = datetime.today()
            products = []
            for b in self.bonds:
                try:
                    maturity = datetime.strptime(b["bondExprDt"], "%Y-%m-%d")
                    years = (maturity - today).days // 365
                    if years * 12 <= period:
                        products.append(b)
                except:
                    continue
            return sorted(products, key=lambda x: x.get("bondSrfcInrt", 0), reverse=True)
        elif product_type == "etf":
            return sorted(self.etfs, key=lambda x: x.get("yield", 0), reverse=True)
        return []

    def calculate_future_value(self, principal, rate, months):
        """복리 계산"""
        if rate == 0 or months == 0:
            return principal
        years = months / 12
        return principal * ((1 + rate/100) ** years)

    def recommend_portfolio(self, risk_level: RiskLevel, target_amount: int, period: int):
        """GPT 기반 포트폴리오 추천 메인 함수"""

        # 1. GPT로 자산배분 결정
        allocation, reasoning = self.get_gpt_allocation(risk_level, target_amount, period)

        # 2. 각 자산군별 상품 선택 및 수익 계산
        recommended = {}
        expected_total = 0

        for ptype, percent in allocation.items():
            invest_amount = target_amount * (percent / 100)
            products = self.filter_products(ptype, period)[:3]  # 상위 3개
            recommended[ptype] = []

            for prod in products:
                if ptype in ["deposit", "saving"]:
                    rate = prod.get("bestRate", 0)
                    fv = self.calculate_future_value(invest_amount, rate, period)
                elif ptype == "bond":
                    rate = prod.get("bondSrfcInrt", 0)
                    fv = self.calculate_future_value(invest_amount, rate, period)
                else:  # etf
                    rate = prod.get("yield", 7)
                    fv = self.calculate_future_value(invest_amount, rate, period)

                expected_total += fv / len(products) if products else 0

                # term 필드를 문자열로 변환
                term_value = prod.get("bestTerm") or prod.get("bondExprDt", "기간 정보 없음")
                if isinstance(term_value, (int, float)):
                    term_str = f"{term_value}개월"
                else:
                    term_str = str(term_value)

                recommended[ptype].append({
                    "name": (prod.get("productName") or
                            prod.get("isinCdNm") or
                            prod.get("itmsNm", "상품명 없음")),
                    "bank": (prod.get("bankName") or
                            prod.get("bondIsurNm") or
                            prod.get("corpNm", "발행기관 없음")),
                    "rate": rate,
                    "term": term_str,
                    "investAmount": round(invest_amount, 2),
                    "expectedValue": round(fv, 2)
                })

        return {
            "riskLevel": risk_level.value,
            "targetAmount": target_amount,
            "investmentPeriod": period,
            "allocation": allocation,
            "expectedTotal": round(expected_total, 2),
            "recommendedProducts": recommended,
            "gptReasoning": reasoning
        }