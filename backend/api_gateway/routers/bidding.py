from fastapi import APIRouter
from pydantic import BaseModel
from bidding_system.real_time_bidding_engine.engine import optimize_bid, BidResult

router = APIRouter()


class BidRequest(BaseModel):
    property_id: str
    source: str
    ask_price: float
    estimated_monthly_rent: float
    rehab_cost: float
    arv: float
    competition_saturation: float = 0.50
    days_on_market: int = 30
    min_profit_margin: float = 0.08
    loan_rate: float = 0.079
    ltv: float = 0.75


@router.post("/optimize", response_model=BidResult)
async def optimize_bid_endpoint(req: BidRequest) -> BidResult:
    """Compute optimal bid for an auction or wholesaler listing."""
    return optimize_bid(
        property_id=req.property_id,
        source=req.source,
        ask_price=req.ask_price,
        estimated_monthly_rent=req.estimated_monthly_rent,
        rehab_cost=req.rehab_cost,
        arv=req.arv,
        competition_saturation=req.competition_saturation,
        days_on_market=req.days_on_market,
        min_profit_margin=req.min_profit_margin,
        loan_rate=req.loan_rate,
        ltv=req.ltv,
    )
