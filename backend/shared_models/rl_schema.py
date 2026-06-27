"""
RL training data schema — the temporal backbone for policy learning.

State/Action/Reward/NextState tuples must be stored per timestep so
the agent can learn from delayed reward realization (rent, rehab, appreciation).
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RLAction(str, Enum):
    BUY = "BUY"
    REJECT = "REJECT"
    HOLD = "HOLD"
    INCREASE_BID = "INCREASE_BID"
    DECREASE_BID = "DECREASE_BID"


class PropertyFeatures(BaseModel):
    sqft: float
    year_built: int
    condition_score: float
    zip_code: str
    property_type: str
    bedrooms: int
    bathrooms: float


class FinancialFeatures(BaseModel):
    purchase_price: float
    dscr_base: float
    dscr_stress: float
    noi: float
    loan_to_value: float
    cap_rate: float
    cash_on_cash_return: float
    irr_estimate: float


class MarketFeatures(BaseModel):
    zip_investor_activity: float
    rent_growth_yoy: float
    vacancy_rate: float
    zip_liquidity_index: float
    zip_institutional_presence: float
    days_on_market: int
    macro_regime: str


class LenderFeatures(BaseModel):
    approval_probability: float
    max_ltv_available: float
    best_available_rate: float
    num_approved_lenders: int
    financing_viable: bool


class PortfolioState(BaseModel):
    available_cash: float
    total_deployed_capital: float
    num_active_properties: int
    portfolio_dscr: float
    zip_exposure: dict[str, float]
    state_exposure: dict[str, float]
    max_single_asset_pct: float
    current_drawdown: float


class RLState(BaseModel):
    """Full state vector at decision time t."""
    timestamp: datetime
    property_id: str
    property_features: PropertyFeatures
    financial_features: FinancialFeatures
    market_features: MarketFeatures
    lender_features: LenderFeatures
    portfolio_state: PortfolioState

    def to_flat_vector(self) -> list[float]:
        """Flatten to numeric vector for model input."""
        pf = self.property_features
        ff = self.financial_features
        mf = self.market_features
        lf = self.lender_features
        ps = self.portfolio_state

        return [
            pf.sqft / 10000,
            pf.year_built / 2024,
            pf.condition_score,
            pf.bedrooms / 10,
            pf.bathrooms / 5,
            ff.purchase_price / 1_000_000,
            ff.dscr_base,
            ff.dscr_stress,
            ff.noi / 100_000,
            ff.loan_to_value,
            ff.cap_rate,
            ff.cash_on_cash_return,
            ff.irr_estimate,
            mf.zip_investor_activity,
            mf.rent_growth_yoy,
            mf.vacancy_rate,
            mf.zip_liquidity_index,
            mf.zip_institutional_presence,
            mf.days_on_market / 365,
            lf.approval_probability,
            lf.max_ltv_available,
            lf.best_available_rate,
            lf.num_approved_lenders / 10,
            float(lf.financing_viable),
            ps.available_cash / 10_000_000,
            ps.total_deployed_capital / 10_000_000,
            ps.num_active_properties / 100,
            ps.portfolio_dscr,
            ps.max_single_asset_pct,
            ps.current_drawdown,
        ]


class RLReward(BaseModel):
    """Realized reward components — populated as outcomes are observed."""
    timesteps_elapsed: int
    cash_flow_realized: float = 0.0
    appreciation_gain: float = 0.0
    refinance_gain: float = 0.0
    vacancy_loss: float = 0.0
    rehab_overrun: float = 0.0
    default_loss: float = 0.0
    illiquidity_penalty: float = 0.0
    drawdown_penalty: float = 0.0
    diversification_bonus: float = 0.0
    discount_rate: float = 0.08

    @property
    def total_reward(self) -> float:
        discount = (1 - self.discount_rate) ** self.timesteps_elapsed
        raw = (
            self.cash_flow_realized
            + self.appreciation_gain
            + self.refinance_gain
            + self.diversification_bonus
            - self.vacancy_loss
            - self.rehab_overrun
            - self.default_loss
            - self.illiquidity_penalty
            - self.drawdown_penalty
        )
        return raw * discount


class RLTransition(BaseModel):
    """Single SARS' tuple stored to replay buffer for training."""
    episode_id: str
    step: int
    state: RLState
    action: RLAction
    reward: Optional[RLReward] = None
    next_state: Optional[RLState] = None
    done: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
