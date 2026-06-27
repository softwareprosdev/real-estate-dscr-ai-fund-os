from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UnderwritingInput(BaseModel):
    property_id: str
    purchase_price: float
    arv: float
    estimated_monthly_rent: float
    section_8_rent: Optional[float] = None
    rehab_cost_estimate: float = 0.0
    loan_amount: Optional[float] = None
    loan_rate: float = 0.0799  # Kiavi/Visio 30yr DSCR, June 2025
    loan_term_years: int = 30
    ltv: float = 0.75
    vacancy_rate: float = 0.08
    property_tax_annual: Optional[float] = None
    insurance_annual: Optional[float] = None
    property_mgmt_rate: float = 0.10
    maintenance_rate: float = 0.05
    capex_rate: float = 0.05


class DSCRResult(BaseModel):
    property_id: str
    purchase_price: float
    loan_amount: float
    monthly_payment: float
    annual_debt_service: float

    gross_rent: float
    effective_gross_income: float
    operating_expenses: float
    noi: float

    dscr_base: float
    dscr_stress_rate_plus_200bps: float
    dscr_stress_vacancy_plus_10pct: float
    dscr_combined_stress: float

    cash_flow_monthly: float
    cash_flow_annual: float
    cash_on_cash_return: float
    cap_rate: float

    irr_5yr_estimate: float
    risk_adjusted_return: float

    underwritten_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def passes_dscr_threshold(self) -> bool:
        return self.dscr_base >= 1.20

    @property
    def passes_stress_threshold(self) -> bool:
        return self.dscr_combined_stress >= 1.05


class RiskFlag(BaseModel):
    flag_type: str
    severity: str
    message: str
    value: Optional[float] = None


class UnderwritingReport(BaseModel):
    property_id: str
    dscr_result: DSCRResult
    risk_flags: list[RiskFlag]
    recommendation: str
    underwriting_confidence: float = Field(ge=0.0, le=1.0)
