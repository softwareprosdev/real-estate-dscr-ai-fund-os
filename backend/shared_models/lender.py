from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LenderType(str, Enum):
    CONSERVATIVE_BANK = "conservative_bank"
    DSCR_SPECIALIST = "dscr_specialist"
    AGGRESSIVE_PORTFOLIO = "aggressive_portfolio"
    PRIVATE_BRIDGE = "private_bridge"
    CREDIT_UNION = "credit_union"


class LenderProfile(BaseModel):
    lender_id: str
    lender_name: str
    lender_type: LenderType

    dscr_min: float = Field(ge=1.0, le=2.0)
    dscr_stress_min: float = Field(ge=0.7, le=1.5)
    ltv_max: float = Field(ge=0.5, le=0.85)
    loan_min: float = 50_000
    loan_max: float = 5_000_000

    property_condition_min_score: float = Field(ge=0.0, le=1.0)
    zip_risk_sensitivity: float = Field(ge=0.0, le=1.0)
    property_age_sensitivity: float = Field(ge=0.0, le=1.0)
    loan_size_sensitivity: float = Field(ge=0.0, le=1.0)

    base_rate: float
    rate_spread_bps: int = 0

    class Config:
        use_enum_values = True


class LenderDecisionInput(BaseModel):
    property_id: str
    lender_id: str
    dscr_base: float
    dscr_stress: float
    ltv: float
    loan_amount: float
    property_condition_score: float
    zip_code: str
    zip_liquidity_index: float
    rehab_risk_score: float
    year_built: int


class LenderDecision(BaseModel):
    property_id: str
    lender_id: str
    lender_name: str
    approval_probability: float = Field(ge=0.0, le=1.0)
    approved: bool
    denial_reasons: list[str] = Field(default_factory=list)
    offered_rate: Optional[float] = None
    offered_ltv: Optional[float] = None
    max_loan_amount: Optional[float] = None
    decided_at: datetime = Field(default_factory=datetime.utcnow)


class LenderApprovalSummary(BaseModel):
    property_id: str
    approval_probability: float
    approved_lenders: list[str]
    denied_lenders: list[str]
    best_rate: Optional[float] = None
    max_ltv_available: float
    risk_flags: list[str] = Field(default_factory=list)
    financing_viable: bool
