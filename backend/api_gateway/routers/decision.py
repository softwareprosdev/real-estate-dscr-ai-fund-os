from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.shared_models.underwriting import UnderwritingInput
from backend.shared_models.lender import LenderDecisionInput
from core.underwriting_engine.engine import underwrite
from lender_simulator.approval_predictor.predictor import predict_all_lenders
from ml.rehab_model.estimator import estimate_rehab
from ai_agent.decision_engine.engine import (
    decide,
    DecisionOutput,
    MarketContext,
    PortfolioConstraints,
)

router = APIRouter()


class FullDecisionRequest(BaseModel):
    underwriting_input: UnderwritingInput
    lender_input: LenderDecisionInput
    sqft: float
    condition: str
    property_type: str
    year_built: int
    zip_code: str
    state: str
    market_investor_activity: float = 0.50
    market_liquidity_index: float = 0.60
    days_on_market: int = 45
    competition_saturation: float = 0.40
    macro_regime: str = "expansion"
    available_cash: float = 2_000_000.0
    zip_exposure_pct: dict[str, float] = {}


@router.post("/analyze", response_model=DecisionOutput)
async def full_decision(req: FullDecisionRequest) -> DecisionOutput:
    """
    One-shot full decision: underwrite + lender sim + rehab estimate + BUY/REJECT/HOLD.
    """
    underwriting_report = underwrite(req.underwriting_input)
    lender_summary = predict_all_lenders(req.lender_input)
    rehab = estimate_rehab(
        property_id=req.underwriting_input.property_id,
        sqft=req.sqft,
        condition=req.condition,
        property_type=req.property_type,
        year_built=req.year_built,
    )
    market = MarketContext(
        zip_investor_activity=req.market_investor_activity,
        zip_liquidity_index=req.market_liquidity_index,
        days_on_market=req.days_on_market,
        competition_saturation=req.competition_saturation,
        macro_regime=req.macro_regime,
    )
    constraints = PortfolioConstraints(
        available_cash=req.available_cash,
        zip_exposure_pct=req.zip_exposure_pct,
    )
    return decide(
        underwriting=underwriting_report,
        lender_summary=lender_summary,
        rehab=rehab,
        market=market,
        constraints=constraints,
        zip_code=req.zip_code,
        state=req.state,
    )
