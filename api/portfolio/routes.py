from fastapi import APIRouter, HTTPException, Depends
from .models import PortfolioRequest, PortfolioResponse, RiskLevel
from .services import PortfolioService
import os

router = APIRouter()

def get_portfolio_service():
    """포트폴리오 서비스 의존성 주입"""
    try:
        return PortfolioService()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"포트폴리오 서비스 초기화 실패: {str(e)}")

@router.post("/recommend", response_model=PortfolioResponse)
async def recommend_portfolio(
    request: PortfolioRequest,
    service: PortfolioService = Depends(get_portfolio_service)
):
    """
    GPT 기반 포트폴리오 추천 API

    - **risk_level**: 투자자 위험성향 (안정형, 안정추구형, 위험중립형, 적극투자형, 공격투자형)
    - **target_amount**: 목표 투자금액 (원)
    - **period**: 투자기간 (개월)
    """
    try:
        result = service.recommend_portfolio(
            risk_level=request.risk_level,
            target_amount=request.target_amount,
            period=request.period
        )
        return PortfolioResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"포트폴리오 추천 실패: {str(e)}")

@router.get("/risk-levels")
async def get_risk_levels():
    """
    사용 가능한 위험성향 목록 반환
    """
    return {
        "risk_levels": [
            {"value": "안정형", "description": "안전한 투자를 선호, 원금 보장 중시"},
            {"value": "안정추구형", "description": "약간의 위험을 감수하며 안정적 수익 추구"},
            {"value": "위험중립형", "description": "적정 수준의 위험과 수익을 균형있게 추구"},
            {"value": "적극투자형", "description": "높은 수익을 위해 상당한 위험 감수"},
            {"value": "공격투자형", "description": "최대 수익을 위해 높은 위험도 적극 감수"}
        ]
    }

@router.get("/health")
async def health_check():
    """
    포트폴리오 API 상태 확인
    """
    return {
        "status": "healthy",
        "service": "portfolio_recommendation",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
    }