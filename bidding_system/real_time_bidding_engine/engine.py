"""
Real-time bidding engine for auctions and wholesaler negotiations.

Bid optimization logic:
- Max bid = price at which DSCR drops to minimum threshold
- Win probability is estimated from ZIP competition data
- Bid is optimized to maximize expected value (win_prob * deal_value)
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from core.underwriting_engine.engine import underwrite
from backend.shared_models.underwriting import UnderwritingInput


@dataclass
class BidResult:
    property_id: str
    source: str
    current_ask: float
    max_allowable_bid: float
    recommended_bid: float
    expected_profit_at_bid: float
    win_probability: float
    expected_value: float
    bid_strategy: str
    reasoning: list[str]


def calculate_max_allowable_bid(
    property_id: str,
    estimated_monthly_rent: float,
    rehab_cost: float,
    loan_rate: float = 0.079,
    ltv: float = 0.75,
    target_dscr: float = 1.20,
    vacancy_rate: float = 0.08,
    property_mgmt_rate: float = 0.10,
    maintenance_rate: float = 0.05,
    capex_rate: float = 0.05,
    arv: float = 0.0,
) -> float:
    """
    Binary search for max bid price that still clears target DSCR.
    """
    low, high = 10_000.0, 5_000_000.0
    target = arv if arv > 0 else estimated_monthly_rent * 12 / 0.07

    for _ in range(50):
        mid = (low + high) / 2
        inp = UnderwritingInput(
            property_id=property_id,
            purchase_price=mid,
            arv=arv or mid,
            estimated_monthly_rent=estimated_monthly_rent,
            rehab_cost_estimate=rehab_cost,
            loan_rate=loan_rate,
            ltv=ltv,
            vacancy_rate=vacancy_rate,
            property_mgmt_rate=property_mgmt_rate,
            maintenance_rate=maintenance_rate,
            capex_rate=capex_rate,
        )
        result = underwrite(inp)
        if result.dscr_result.dscr_base > target_dscr:
            low = mid
        else:
            high = mid
        if high - low < 500:
            break

    return round(low, -2)


def _win_probability(
    bid: float,
    ask_price: float,
    competition_saturation: float,
    days_on_market: int,
) -> float:
    bid_ratio = bid / ask_price
    base_win_prob = 1.0 / (1.0 + math.exp(-8 * (bid_ratio - 0.95)))
    competition_discount = competition_saturation * 0.20
    dom_bonus = min(0.10, days_on_market / 1000)
    return min(0.95, max(0.02, base_win_prob - competition_discount + dom_bonus))


def optimize_bid(
    property_id: str,
    source: str,
    ask_price: float,
    estimated_monthly_rent: float,
    rehab_cost: float,
    arv: float,
    competition_saturation: float = 0.50,
    days_on_market: int = 30,
    min_profit_margin: float = 0.08,
    loan_rate: float = 0.079,
    ltv: float = 0.75,
) -> BidResult:
    max_bid = calculate_max_allowable_bid(
        property_id=property_id,
        estimated_monthly_rent=estimated_monthly_rent,
        rehab_cost=rehab_cost,
        loan_rate=loan_rate,
        ltv=ltv,
        arv=arv,
    )

    reasoning: list[str] = []
    strategy = "standard"

    # Apply profit margin constraint
    margin_ceiling = arv * (1 - min_profit_margin) - rehab_cost if arv > 0 else max_bid
    if margin_ceiling <= 0:
        return BidResult(
            property_id=property_id,
            source=source,
            current_ask=ask_price,
            max_allowable_bid=0.0,
            recommended_bid=0.0,
            expected_profit_at_bid=0.0,
            win_probability=0.0,
            expected_value=0.0,
            bid_strategy="no_bid",
            reasoning=["Deal unviable — rehab cost exceeds ARV profit margin; no positive bid is justified"],
        )
    effective_max = min(max_bid, margin_ceiling)

    if ask_price > effective_max:
        recommended_bid = effective_max
        reasoning.append(f"Ask ${ask_price:,.0f} exceeds DSCR max ${effective_max:,.0f} — bidding max allowable")
        strategy = "max_dscr_bid"
    elif competition_saturation > 0.70:
        recommended_bid = ask_price * 0.93
        reasoning.append("High competition — bidding 7% below ask to protect returns")
        strategy = "competitive_discount"
    elif days_on_market > 60:
        recommended_bid = ask_price * 0.88
        reasoning.append(f"DOM {days_on_market} days — motivated seller, bidding 12% below ask")
        strategy = "motivated_seller_discount"
    else:
        recommended_bid = ask_price * 0.95
        reasoning.append("Normal market conditions — bidding 5% below ask")
        strategy = "standard"

    recommended_bid = min(recommended_bid, effective_max)

    win_prob = _win_probability(recommended_bid, ask_price, competition_saturation, days_on_market)

    equity = recommended_bid * (1 - ltv) + rehab_cost
    deal_value = (arv - recommended_bid - rehab_cost) * 0.6 if arv > 0 else 0
    expected_value = win_prob * deal_value

    return BidResult(
        property_id=property_id,
        source=source,
        current_ask=ask_price,
        max_allowable_bid=effective_max,
        recommended_bid=round(recommended_bid, -2),
        expected_profit_at_bid=round(deal_value, 0),
        win_probability=round(win_prob, 3),
        expected_value=round(expected_value, 0),
        bid_strategy=strategy,
        reasoning=reasoning,
    )
