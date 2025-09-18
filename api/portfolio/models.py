from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

class RiskLevel(str, Enum):
    STABLE = "안정형"
    STABILITY_SEEKING = "안정추구형"
    RISK_NEUTRAL = "위험중립형"
    ACTIVE_INVESTMENT = "적극투자형"
    AGGRESSIVE_INVESTMENT = "공격투자형"

class PortfolioRequest(BaseModel):
    risk_level: RiskLevel = Field(..., description="투자자 위험성향")
    target_amount: int = Field(..., gt=0, description="목표 투자금액 (원)")
    period: int = Field(..., gt=0, description="투자기간 (개월)")

class ProductInfo(BaseModel):
    name: str
    bank: str
    rate: float
    term: str
    investAmount: float
    expectedValue: float

class PortfolioResponse(BaseModel):
    riskLevel: str
    targetAmount: int
    investmentPeriod: int
    allocation: Dict[str, int]
    expectedTotal: float
    recommendedProducts: Dict[str, List[ProductInfo]]
    gptReasoning: str