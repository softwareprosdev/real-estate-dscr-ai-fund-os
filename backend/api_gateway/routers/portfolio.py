from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class PortfolioSummary(BaseModel):
    total_properties: int
    total_deployed_capital: float
    portfolio_noi: float
    portfolio_dscr: float
    total_monthly_cash_flow: float
    avg_coc_return: float
    zip_concentration: dict[str, float]
    state_concentration: dict[str, float]


_mock_portfolio = {
    "total_properties": 0,
    "total_deployed_capital": 0.0,
    "portfolio_noi": 0.0,
    "portfolio_dscr": 0.0,
    "total_monthly_cash_flow": 0.0,
    "avg_coc_return": 0.0,
    "zip_concentration": {},
    "state_concentration": {},
}


@router.get("/summary", response_model=PortfolioSummary)
async def portfolio_summary() -> PortfolioSummary:
    """Current portfolio summary metrics."""
    return PortfolioSummary(**_mock_portfolio)
