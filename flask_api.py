from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
from dotenv import load_dotenv
import json
from pathlib import Path
from enum import Enum 
from datetime import datetime

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)
CORS(app)

# 전역 챗봇 변수
chatbot = None
recommender = None

# RiskLevel enum 정의
class RiskLevel(Enum):
    STABLE = "안정형"
    STABILITY_SEEKING = "안정추구형"
    RISK_NEUTRAL = "위험중립형"
    ACTIVE_INVESTMENT = "적극투자형"
    AGGRESSIVE_INVESTMENT = "공격투자형"

class EconomicChatbot:
    def __init__(self, api_key, vectorstore_path="economic_terms_faiss"):
        self.api_key = api_key
        self.vectorstore_path = vectorstore_path
        
        # 임베딩 모델 초기화
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=self.api_key
        )
        
        # 벡터스토어 로드
        self.vectorstore = FAISS.load_local(
            self.vectorstore_path, 
            self.embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # 검색기 설정
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        
        # QA 체인 구성
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(
                model="gpt-3.5-turbo", 
                temperature=0, 
                openai_api_key=self.api_key
            ),
            retriever=self.retriever,
            return_source_documents=True
        )
    
    def get_answer(self, question):
        # 질문에 대한 답변 생성
        try:
            response = self.qa_chain.invoke({"query": question})
            
            # 관련 용어들 추출
            related_terms = []
            if response.get('source_documents'):
                for doc in response['source_documents']:
                    term = doc.metadata.get('term', '')
                    if term and term not in related_terms:
                        related_terms.append(term)
            
            return {
                "success": True,
                "answer": response['result'],
                "related_terms": related_terms[:5],
                "source_count": len(response.get('source_documents', []))
            }
            
        except Exception as e:
            return {
                "success": False,
                "answer": f"답변 생성 중 오류가 발생했습니다: {str(e)}",
                "related_terms": [],
                "source_count": 0
            }
    
    def find_similar_terms(self, search_term, count=5):
        # 유사한 용어들 검색
        try:
            docs = self.vectorstore.similarity_search(search_term, k=count)
            results = []
            
            for doc in docs:
                term_name = doc.metadata.get('term', '')
                if term_name:
                    content = doc.page_content
                    if len(content) > 200:
                        content = content[:200] + "..."
                    
                    results.append({
                        "term": term_name,
                        "content": content
                    })
            
            return {"success": True, "terms": results}
            
        except Exception as e:
            return {"success": False, "error": str(e), "terms": []}

# GPT 추천으로 변경하고 주석
# class PortfolioRecommender:
#     def __init__(self, dataset_path="./recommend/financial_portfolio_dataset.json"):
#         print(f"포트폴리오 추천기 초기화 중... 데이터 파일: {dataset_path}")
        
#         try:
#             with open(Path(dataset_path), "r", encoding="utf-8") as f:
#                 self.data = json.load(f)
#             print(f"데이터 파일 로드 성공: {dataset_path}")
#         except FileNotFoundError:
#             print(f"{dataset_path} 파일을 찾을 수 없습니다.")
#             raise FileNotFoundError(f"필수 데이터 파일이 없습니다: {dataset_path}")

#         # 데이터 분리
#         self.savings = self.data.get("savings", [])
#         self.deposits = self.data.get("deposits", [])
#         bonds_data = self.data.get("bonds", {})
#         self.bonds = bonds_data.get("sortByInterest", []) + bonds_data.get("sortByMaturity", [])
#         self.etfs = self.data.get("etfs", [])
        
#         print(f"데이터 로드 완료:")
#         print(f"  - 적금: {len(self.savings)}개")
#         print(f"  - 예금: {len(self.deposits)}개") 
#         print(f"  - 채권: {len(self.bonds)}개")
#         print(f"  - ETF: {len(self.etfs)}개")

#     def _create_dummy_data(self):
#         # 더미 데이터 생성 - 사용하지 않음
#         pass

#     def get_allocation(self, risk_level: RiskLevel):
#         # 리스크 레벨별 자산 배분 비율 (4개 상품군 고정)
#         mapping = {
#             RiskLevel.STABLE: {"deposit": 40, "saving": 30, "bond": 20, "etf": 10},
#             RiskLevel.STABILITY_SEEKING: {"deposit": 30, "saving": 25, "bond": 25, "etf": 20},
#             RiskLevel.RISK_NEUTRAL: {"deposit": 20, "saving": 20, "bond": 30, "etf": 30},
#             RiskLevel.ACTIVE_INVESTMENT: {"deposit": 10, "saving": 15, "bond": 25, "etf": 50},
#             RiskLevel.AGGRESSIVE_INVESTMENT: {"deposit": 5, "saving": 10, "bond": 15, "etf": 70},
#         }
#         return mapping.get(risk_level, {"deposit": 25, "saving": 25, "bond": 25, "etf": 25})

#     def filter_products(self, product_type: str, period: int):
#         # 기간에 맞는 상품 필터링 후 금리순 정렬
#         if product_type == "deposit":
#             products = sorted(self.deposits, key=lambda x: x.get("bestRate", 0), reverse=True)
#             return [p for p in products if p.get("bestTerm", 0) <= period]
#         elif product_type == "saving":
#             products = sorted(self.savings, key=lambda x: x.get("bestRate", 0), reverse=True)
#             return [p for p in products if p.get("bestTerm", 0) <= period]
#         elif product_type == "bond":
#             today = datetime.today()
#             products = []
#             for b in self.bonds:
#                 try:
#                     maturity = datetime.strptime(b["bondExprDt"], "%Y-%m-%d")
#                     years = (maturity - today).days // 365
#                     if years * 12 <= period:
#                         products.append(b)
#                 except:
#                     continue
#             return sorted(products, key=lambda x: x.get("bondSrfcInrt", 0), reverse=True)
#         elif product_type == "etf":
#             return sorted(self.etfs, key=lambda x: x.get("yield", 0), reverse=True)
#         return []

#     def calculate_future_value(self, principal, rate, months):
#         # 단순 복리 계산
#         if rate == 0 or months == 0:
#             return principal
#         years = months / 12
#         return principal * ((1 + rate/100) ** years)

#     def recommend(self, risk_level: RiskLevel, target_amount: int, period: int):
#         print(f"추천 실행: {risk_level.value}, {target_amount:,}원, {period}개월")
        
#         allocation = self.get_allocation(risk_level)
#         recommended = {}
#         expected_total = 0

#         for ptype, percent in allocation.items():
#             invest_amount = target_amount * (percent / 100)
#             products = self.filter_products(ptype, period)[:3]  # 상위 3개
#             recommended[ptype] = []

#             for prod in products:
#                 if ptype in ["deposit", "saving"]:
#                     rate = prod.get("bestRate", 0)
#                     fv = self.calculate_future_value(invest_amount, rate, period)
#                 elif ptype == "bond":
#                     rate = prod.get("bondSrfcInrt", 0)
#                     fv = self.calculate_future_value(invest_amount, rate, period)
#                 else:  # etf
#                     rate = prod.get("yield", 7)  # ETF는 평균 기대수익률 가정
#                     fv = self.calculate_future_value(invest_amount, rate, period)

#                 expected_total += fv / len(products) if products else 0  # 평균값으로 계산
                
#                 recommended[ptype].append({
#                     "name": prod.get("productName") or prod.get("isinCdNm", "상품명 없음"),
#                     "bank": prod.get("bankName") or prod.get("bondIsurNm", "발행기관 없음"),
#                     "rate": rate,
#                     "term": prod.get("bestTerm") or prod.get("bondExprDt", "기간 정보 없음"),
#                     "investAmount": round(invest_amount, 2),
#                     "expectedValue": round(fv, 2)
#                 })

#         result = {
#             "riskLevel": risk_level.value,  # enum의 value 사용
#             "targetAmount": target_amount,
#             "investmentPeriod": period,
#             "allocation": allocation,
#             "expectedTotal": round(expected_total, 2),
#             "recommendedProducts": recommended
#         }
        
#         print(f"추천 완료: 예상수익 {expected_total:,.0f}원")
#         return result

@app.route('/', methods=['GET'])
def health_check():
    # 서버 상태 확인
    return jsonify({
        "status": "running",
        "message": "경제용어 챗봇 및 포트폴리오 추천 API가 정상 동작중입니다",
        "chatbot_status": "초기화됨" if chatbot else "초기화 안됨",
        "recommender_status": "초기화됨" if recommender else "초기화 안됨",
        "endpoints": ["/ask", "/search", "/chat", "/recommend/percent", "/recommend/products"]
    })

@app.route('/ask', methods=['POST'])
def ask_question():
    # 질문-답변 API
    if not chatbot:
        return jsonify({
            "success": False,
            "error": "챗봇이 초기화되지 않았습니다"
        }), 500
        
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                "success": False,
                "error": "question 필드가 필요합니다"
            }), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({
                "success": False,
                "error": "빈 질문은 처리할 수 없습니다"
            }), 400
        
        # 챗봇에게 질문
        result = chatbot.get_answer(question)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}"
        }), 500

@app.route('/recommend/products', methods=['POST'])
def recommend_products():
    # 포트폴리오 상품 추천 API
    if not recommender:
        return jsonify({
            "success": False,
            "error": "포트폴리오 추천기가 초기화되지 않았습니다"
        }), 500
        
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "요청 데이터가 없습니다"
            }), 400
        
        required_fields = ["riskLevel", "targetAmount", "investmentPeriod"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"{field} 필드가 필요합니다"
                }), 400
        
        # RiskLevel enum 변환
        try:
            risk_level = RiskLevel[data["riskLevel"]]
        except KeyError:
            return jsonify({
                "success": False,
                "error": f"유효하지 않은 riskLevel입니다. 사용 가능한 값: {[e.name for e in RiskLevel]}"
            }), 400
        
        target_amount = data["targetAmount"]
        investment_period = data["investmentPeriod"]
        
        if not isinstance(target_amount, (int, float)) or target_amount <= 0:
            return jsonify({
                "success": False,
                "error": "targetAmount는 양수여야 합니다"
            }), 400
            
        if not isinstance(investment_period, int) or investment_period <= 0:
            return jsonify({
                "success": False,
                "error": "investmentPeriod는 양의 정수여야 합니다"
            }), 400

        # 추천 실행
        result = recommender.recommend(risk_level, int(target_amount), investment_period)

        return jsonify({
            "success": True,
            "data": {
                "riskLevel": result["riskLevel"],
                "targetAmount": result["targetAmount"],
                "investmentPeriod": result["investmentPeriod"],
                "allocation": result["allocation"],
                "recommendedProducts": result["recommendedProducts"],
                "expectedTotal": result["expectedTotal"],
                "gptReasoning": result.get("gptReasoning", "")  # GPT 근거 추가
            }
        })

    except Exception as e:
        print(f"상품 추천 에러: {e}")
        import traceback
        traceback.print_exc()

@app.route('/search', methods=['POST'])
def search_terms():
    # 용어 검색 API
    if not chatbot:
        return jsonify({
            "success": False,
            "error": "챗봇이 초기화되지 않았습니다"
        }), 500
        
    try:
        data = request.get_json()
        
        if not data or 'term' not in data:
            return jsonify({
                "success": False,
                "error": "term 필드가 필요합니다"
            }), 400
        
        search_term = data['term'].strip()
        count = data.get('k', 5)  # 'k' 필드 지원
        
        if not search_term:
            return jsonify({
                "success": False,
                "error": "빈 검색어는 처리할 수 없습니다"
            }), 400
        
        # 유사 용어 검색
        result = chatbot.find_similar_terms(search_term, count)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}"
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    # 채팅 API
    if not chatbot:
        return jsonify({
            "success": False,
            "reply": "챗봇이 초기화되지 않았습니다"
        }), 500
        
    try:
        data = request.get_json()
        
        message = data.get('message', '').strip()
        if not message:
            return jsonify({
                "success": False,
                "reply": "메시지를 입력해주세요"
            }), 400
        
        # 챗봇 응답 생성
        result = chatbot.get_answer(message)
        
        return jsonify({
            "success": result['success'],
            "reply": result['answer'],
            "related_terms": result['related_terms'],
            "metadata": {
                "source_count": result['source_count'],
                "user_message": message
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "reply": f"서버에 문제가 발생했습니다: {str(e)}"
        }), 500

@app.route('/recommend/percent', methods=['POST'])
def recommend_percent():
    # 포트폴리오 비율 추천 API
    if not recommender:
        return jsonify({
            "success": False,
            "error": "포트폴리오 추천기가 초기화되지 않았습니다"
        }), 500
        
    try:
        data = request.get_json()
        
        # 필수 필드 검증
        if not data:
            return jsonify({
                "success": False,
                "error": "요청 데이터가 없습니다"
            }), 400
        
        required_fields = ["riskLevel", "targetAmount", "investmentPeriod"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"{field} 필드가 필요합니다"
                }), 400
        
        # RiskLevel enum 변환
        try:
            risk_level = RiskLevel[data["riskLevel"]]
        except KeyError:
            return jsonify({
                "success": False,
                "error": f"유효하지 않은 riskLevel입니다. 사용 가능한 값: {[e.name for e in RiskLevel]}"
            }), 400
        
        target_amount = data["targetAmount"]
        investment_period = data["investmentPeriod"]
        
        # 입력값 검증
        if not isinstance(target_amount, (int, float)) or target_amount <= 0:
            return jsonify({
                "success": False,
                "error": "targetAmount는 양수여야 합니다"
            }), 400
            
        if not isinstance(investment_period, int) or investment_period <= 0:
            return jsonify({
                "success": False,
                "error": "investmentPeriod는 양의 정수여야 합니다"
            }), 400

        # 추천 실행
        result = recommender.recommend(risk_level, int(target_amount), investment_period)

        return jsonify({
            "success": True,
            "data": {
                "riskLevel": result["riskLevel"],
                "targetAmount": result["targetAmount"],
                "investmentPeriod": result["investmentPeriod"],
                "allocation": result["allocation"],
                "expectedTotal": result["expectedTotal"],
                "gptReasoning": result.get("gptReasoning", "")  # GPT 근거가 있으면 포함, 없으면 빈 문자열
            }
        })

    except Exception as e:
        print(f"추천 에러: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}"
        }), 500

def setup_chatbot():
    # 챗봇 초기화
    global chatbot
    
    try:
        # API 키 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("경고: OPENAI_API_KEY 환경변수가 설정되지 않았습니다. 챗봇 기능이 비활성화됩니다.")
            return
        
        # 벡터스토어 경로 확인
        vectorstore_path = "economic_terms_faiss"
        if not os.path.exists(vectorstore_path):
            print(f"경고: 벡터스토어 폴더를 찾을 수 없습니다: {vectorstore_path}. 챗봇 기능이 비활성화됩니다.")
            return
        
        # 챗봇 초기화
        print("챗봇 초기화 중...")
        chatbot = EconomicChatbot(api_key, vectorstore_path)
        print("경제용어 챗봇 초기화 완료")
        
    except Exception as e:
        print(f"경고: 챗봇 초기화 실패: {e}")
        print("챗봇 기능이 비활성화되지만 서버는 계속 실행됩니다.")

def setup_recommender():
    # GPT 포트폴리오 추천기 초기화
    global recommender
    
    try:
        print("GPT 포트폴리오 추천기 초기화 시작...")
        
        # OpenAI API 키 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("OpenAI API 키가 없습니다. 추천 기능이 비활성화됩니다.")
            recommender = None
            return
        
        # GPT 추천기 사용
        from recommend.recommender import GPTPortfolioRecommender
        recommender = GPTPortfolioRecommender(openai_api_key=api_key)
        print("GPT 포트폴리오 추천기 초기화 완료")
        
    except Exception as e:
        print(f"GPT 추천기 초기화 실패: {e}")
        recommender = None

if __name__ == '__main__':
    print("Flask 서버 시작...")
    
    # 포트폴리오 추천기 설정 (필수)
    setup_recommender()
    
    # 챗봇 설정 (선택적)
    setup_chatbot()
    
    # 서버 실행
    print("서버 상태:")
    print(f"  - 챗봇: {'초기화됨' if chatbot else '비활성화'}")
    print(f"  - 추천기: {'초기화됨' if recommender else '비활성화'}")
    print("\nFlask 서버 시작...")
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )