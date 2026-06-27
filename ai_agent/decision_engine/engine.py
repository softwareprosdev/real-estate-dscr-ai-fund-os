"""
Autonomous acquisition decision engine.

Integrates underwriting, lender approval, rehab estimates,
market intelligence, and portfolio constraints into a final BUY/REJECT/HOLD decision.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from backend.shared_models.underwriting import UnderwritingReport
from backend.shared_models.lender import LenderApprovalSummary
from ml.rehab_model.estimator import RehabEstimate


@dataclass
class PortfolioConstraints:
    available_cash: float
    max_single_deal_pct: float = 0.20
    zip_exposure_pct: dict[str, float] = field(default_factory=dict)
    state_exposure_pct: dict[str, float] = field(default_factory=dict)
    zip_limit: float = 0.30
    state_limit: float = 0.50
    min_portfolio_dscr: float = 1.20


@dataclass
class MarketContext:
    zip_investor_activity: float
    zip_liquidity_index: float
    days_on_market: int
    competition_saturation: float
    macro_regime: str


@dataclass
class DecisionOutput:
    property_id: str
    decision: str
    confidence: float
    position_size: float
    recommended_bid: float
    reasoning: list[str]
    risk_flags: list[str]
    dscr_summary: dict
    lender_summary: dict


def decide(
    underwriting: UnderwritingReport,
    lender_summary: LenderApprovalSummary,
    rehab: RehabEstimate,
    market: MarketContext,
    constraints: PortfolioConstraints,
    zip_code: str,
    state: str,
) -> DecisionOutput:
    reasoning: list[str] = []
    risk_flags: list[str] = []
    score = 0.0

    dscr = underwriting.dscr_result

    # === HARD KILLS ===
    if underwriting.recommendation == "REJECT":
        return DecisionOutput(
            property_id=underwriting.property_id,
            decision="REJECT",
            confidence=0.95,
            position_size=0.0,
            recommended_bid=0.0,
            reasoning=["Underwriting hard reject — DSCR critically insufficient"],
            risk_flags=[f.message for f in underwriting.risk_flags],
            dscr_summary={"dscr_base": dscr.dscr_base, "recommendation": underwriting.recommendation},
            lender_summary={"financing_viable": lender_summary.financing_viable},
        )

    if not lender_summary.financing_viable:
        risk_flags.append("No lenders approved — cash deal required or deal unviable")
        if constraints.available_cash < dscr.purchase_price:
            return DecisionOutput(
                property_id=underwriting.property_id,
                decision="REJECT",
                confidence=0.90,
                position_size=0.0,
                recommended_bid=0.0,
                reasoning=["Unfinanceable and insufficient cash for outright purchase"],
                risk_flags=risk_flags,
                dscr_summary={},
                lender_summary={},
            )

    # === CAPITAL CONSTRAINTS ===
    equity_required = dscr.purchase_price * (1 - (lender_summary.max_ltv_available or 0.75))
    equity_required += rehab.base_estimate
    equity_pct_of_cash = equity_required / constraints.available_cash if constraints.available_cash > 0 else 1.0

    if equity_pct_of_cash > constraints.max_single_deal_pct:
        risk_flags.append(f"Deal requires {equity_pct_of_cash:.0%} of available cash — exceeds {constraints.max_single_deal_pct:.0%} single-deal limit")
        score -= 20

    current_zip_pct = constraints.zip_exposure_pct.get(zip_code, 0.0)
    if current_zip_pct + (equity_required / constraints.available_cash) > constraints.zip_limit:
        risk_flags.append(f"ZIP {zip_code} would breach {constraints.zip_limit:.0%} concentration limit")
        score -= 15

    # === DSCR SCORING ===
    if dscr.dscr_base >= 1.35:
        score += 30
        reasoning.append(f"Strong DSCR {dscr.dscr_base:.2f} — well above 1.35 institutional threshold")
    elif dscr.dscr_base >= 1.25:
        score += 20
        reasoning.append(f"Solid DSCR {dscr.dscr_base:.2f}")
    elif dscr.dscr_base >= 1.20:
        score += 10
        reasoning.append(f"Acceptable DSCR {dscr.dscr_base:.2f} — at minimum threshold")
    else:
        score -= 10

    if dscr.dscr_combined_stress >= 1.10:
        score += 15
        reasoning.append("Stress DSCR strong — survives rate+vacancy shock")
    elif dscr.dscr_combined_stress >= 1.05:
        score += 5
    else:
        score -= 10
        risk_flags.append(f"Stress DSCR {dscr.dscr_combined_stress:.2f} dangerously low")

    # === RETURN SCORING ===
    if dscr.cash_on_cash_return >= 0.10:
        score += 20
        reasoning.append(f"Excellent CoC return {dscr.cash_on_cash_return:.1%}")
    elif dscr.cash_on_cash_return >= 0.07:
        score += 10
    elif dscr.cash_on_cash_return < 0.04:
        score -= 10

    # === LENDER SCORING ===
    if lender_summary.approval_probability >= 0.80:
        score += 15
        reasoning.append(f"High lender approval probability {lender_summary.approval_probability:.0%}")
    elif lender_summary.approval_probability >= 0.60:
        score += 5
    else:
        score -= 10
        risk_flags.append(f"Low lender approval probability {lender_summary.approval_probability:.0%}")

    # === MARKET SCORING ===
    if market.competition_saturation < 0.30:
        score += 10
        reasoning.append("Low competitive saturation in this ZIP")
    elif market.competition_saturation > 0.70:
        score -= 10
        risk_flags.append("High investor saturation — may compress future appreciation")

    if market.days_on_market > 90:
        score += 5
        reasoning.append(f"DOM {market.days_on_market} days — motivated seller, negotiation leverage")

    if market.macro_regime in ("recession", "high_rate_compression"):
        score -= 10
        risk_flags.append(f"Adverse macro regime: {market.macro_regime}")

    # === REHAB RISK ===
    if rehab.high_estimate / dscr.purchase_price > 0.35:
        score -= 15
        risk_flags.append(f"Rehab high estimate {rehab.high_estimate:,.0f} is >{35:.0f}% of price — execution risk")
    elif rehab.base_estimate / dscr.purchase_price < 0.10:
        score += 5
        reasoning.append("Light rehab — low execution risk")

    # === FINAL DECISION ===
    if score >= 50:
        decision = "BUY"
        confidence = min(0.95, 0.60 + score / 200)
    elif score >= 25:
        decision = "BUY"
        confidence = min(0.80, 0.50 + score / 200)
    elif score >= 0:
        decision = "CONDITIONAL"
        confidence = 0.55
    else:
        decision = "REJECT"
        confidence = min(0.95, 0.60 + abs(score) / 200)

    position_size = 0.0
    recommended_bid = 0.0
    if decision in ("BUY", "CONDITIONAL"):
        position_size = equity_required
        recommended_bid = dscr.purchase_price * (1 - max(0, (score - 50) / 500))

    return DecisionOutput(
        property_id=underwriting.property_id,
        decision=decision,
        confidence=round(confidence, 3),
        position_size=round(position_size, 0),
        recommended_bid=round(recommended_bid, 0),
        reasoning=reasoning,
        risk_flags=risk_flags,
        dscr_summary={
            "dscr_base": dscr.dscr_base,
            "dscr_stress": dscr.dscr_combined_stress,
            "noi": dscr.noi,
            "cash_flow_monthly": dscr.cash_flow_monthly,
            "coc_return": dscr.cash_on_cash_return,
            "irr_5yr": dscr.irr_5yr_estimate,
        },
        lender_summary={
            "approval_probability": lender_summary.approval_probability,
            "approved_lenders": lender_summary.approved_lenders,
            "best_rate": lender_summary.best_rate,
            "max_ltv": lender_summary.max_ltv_available,
            "financing_viable": lender_summary.financing_viable,
        },
    )
