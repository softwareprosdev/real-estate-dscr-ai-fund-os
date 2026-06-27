"""
Institutional DSCR underwriting engine.

All calculations are deterministic — given the same inputs, the same
outputs are produced. RL agent uses these as features, not overrides.
"""
from __future__ import annotations
import math
from backend.shared_models.underwriting import (
    DSCRResult,
    RiskFlag,
    UnderwritingInput,
    UnderwritingReport,
)


STRESS_RATE_SHOCK_BPS = 200
STRESS_VACANCY_SHOCK = 0.10
DISCOUNT_RATE = 0.08
APPRECIATION_RATE_ANNUAL = 0.03


def _monthly_payment(principal: float, annual_rate: float, term_years: int) -> float:
    r = annual_rate / 12
    n = term_years * 12
    if r == 0:
        return principal / n
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


# Effective property tax rates by state (2024 Tax Foundation data)
_STATE_TAX_RATES: dict[str, float] = {
    "NJ": 0.0219, "IL": 0.0202, "CT": 0.0198, "NH": 0.0177,
    "VT": 0.0165, "NY": 0.0145, "WI": 0.0143, "TX": 0.0160,
    "OH": 0.0157, "MI": 0.0141, "PA": 0.0153, "IA": 0.0149,
    "NE": 0.0147, "RI": 0.0142, "MA": 0.0101, "MD": 0.0100,
    "KS": 0.0127, "MO": 0.0091, "IN": 0.0083, "ME": 0.0105,
    "SD": 0.0107, "MN": 0.0100, "OK": 0.0083, "KY": 0.0078,
    "WA": 0.0092, "CO": 0.0051, "FL": 0.0091, "OR": 0.0095,
    "GA": 0.0080, "VA": 0.0074, "NC": 0.0073, "TN": 0.0061,
    "AL": 0.0041, "MS": 0.0065, "AR": 0.0062, "SC": 0.0055,
    "LA": 0.0057, "WV": 0.0057, "AZ": 0.0061, "CA": 0.0071,
    "NV": 0.0055, "UT": 0.0057, "DC": 0.0056, "DE": 0.0055,
    "ID": 0.0063, "MT": 0.0073, "WY": 0.0058, "NM": 0.0072,
    "AK": 0.0098, "HI": 0.0028,
}
_DEFAULT_TAX_RATE = 0.0108  # national avg


def _estimate_property_tax(purchase_price: float, state: str = "unknown") -> float:
    rate = _STATE_TAX_RATES.get(state.upper(), _DEFAULT_TAX_RATE)
    return purchase_price * rate


def _estimate_insurance(purchase_price: float) -> float:
    # Landlord policy (DP-3): 0.75%–1.0% of replacement cost (2024–2025 market)
    # Costs have risen significantly post-2022 due to reinsurance and climate risk
    return purchase_price * 0.0085


def _irr_5yr(
    equity_invested: float,
    annual_cash_flow: float,
    purchase_price: float,
    ltv: float,
    rehab_cost: float,
) -> float:
    loan = purchase_price * ltv
    future_value = (purchase_price + rehab_cost) * (1 + APPRECIATION_RATE_ANNUAL) ** 5
    equity_at_exit = future_value - loan
    cf = [annual_cash_flow] * 5
    cf[-1] += equity_at_exit

    # Newton-Raphson IRR approximation
    rate = 0.10
    for _ in range(100):
        npv = -equity_invested + sum(c / (1 + rate) ** (i + 1) for i, c in enumerate(cf))
        dnpv = sum(-c * (i + 1) / (1 + rate) ** (i + 2) for i, c in enumerate(cf))
        if abs(dnpv) < 1e-10:
            break
        rate -= npv / dnpv
        rate = max(-0.5, min(rate, 5.0))
    return rate


def underwrite(inp: UnderwritingInput) -> UnderwritingReport:
    loan_amount = inp.loan_amount or (inp.purchase_price * inp.ltv)
    effective_ltv = loan_amount / inp.purchase_price

    monthly_payment = _monthly_payment(loan_amount, inp.loan_rate, inp.loan_term_years)
    annual_debt_service = monthly_payment * 12

    # Use higher of market rent and Section 8 rent
    gross_rent_monthly = max(
        inp.estimated_monthly_rent,
        inp.section_8_rent or 0.0,
    )
    gross_rent_annual = gross_rent_monthly * 12

    effective_gross_income = gross_rent_annual * (1 - inp.vacancy_rate)

    prop_tax = inp.property_tax_annual or _estimate_property_tax(inp.purchase_price)
    insurance = inp.insurance_annual or _estimate_insurance(inp.purchase_price)
    prop_mgmt = effective_gross_income * inp.property_mgmt_rate
    maintenance = effective_gross_income * inp.maintenance_rate
    capex = effective_gross_income * inp.capex_rate

    operating_expenses = prop_tax + insurance + prop_mgmt + maintenance + capex
    noi = effective_gross_income - operating_expenses

    dscr_base = noi / annual_debt_service if annual_debt_service > 0 else 0.0

    # Stress 1: +200bps rate shock
    stressed_rate = inp.loan_rate + (STRESS_RATE_SHOCK_BPS / 10_000)
    stressed_payment = _monthly_payment(loan_amount, stressed_rate, inp.loan_term_years)
    dscr_stress_rate = noi / (stressed_payment * 12) if stressed_payment > 0 else 0.0

    # Stress 2: +10% vacancy
    stressed_egi = gross_rent_annual * (1 - inp.vacancy_rate - STRESS_VACANCY_SHOCK)
    stressed_noi_vacancy = stressed_egi - operating_expenses
    dscr_stress_vacancy = stressed_noi_vacancy / annual_debt_service if annual_debt_service > 0 else 0.0

    # Combined stress
    combined_stressed_noi = stressed_egi - operating_expenses
    combined_stressed_ds = stressed_payment * 12
    dscr_combined = combined_stressed_noi / combined_stressed_ds if combined_stressed_ds > 0 else 0.0

    annual_cash_flow = noi - annual_debt_service
    equity_invested = (inp.purchase_price - loan_amount) + inp.rehab_cost_estimate
    coc_return = annual_cash_flow / equity_invested if equity_invested > 0 else 0.0
    cap_rate = noi / inp.purchase_price if inp.purchase_price > 0 else 0.0

    irr = _irr_5yr(
        equity_invested=equity_invested,
        annual_cash_flow=annual_cash_flow,
        purchase_price=inp.purchase_price,
        ltv=effective_ltv,
        rehab_cost=inp.rehab_cost_estimate,
    )

    # Risk-adjusted return: penalize volatility proxied by stress DSCR deviation
    stress_haircut = max(0, (dscr_base - dscr_combined) / dscr_base) if dscr_base > 0 else 1.0
    risk_adjusted_return = irr * (1 - stress_haircut * 0.5)

    dscr_result = DSCRResult(
        property_id=inp.property_id,
        purchase_price=inp.purchase_price,
        loan_amount=loan_amount,
        monthly_payment=monthly_payment,
        annual_debt_service=annual_debt_service,
        gross_rent=gross_rent_annual,
        effective_gross_income=effective_gross_income,
        operating_expenses=operating_expenses,
        noi=noi,
        dscr_base=round(dscr_base, 4),
        dscr_stress_rate_plus_200bps=round(dscr_stress_rate, 4),
        dscr_stress_vacancy_plus_10pct=round(dscr_stress_vacancy, 4),
        dscr_combined_stress=round(dscr_combined, 4),
        cash_flow_monthly=round(annual_cash_flow / 12, 2),
        cash_flow_annual=round(annual_cash_flow, 2),
        cash_on_cash_return=round(coc_return, 4),
        cap_rate=round(cap_rate, 4),
        irr_5yr_estimate=round(irr, 4),
        risk_adjusted_return=round(risk_adjusted_return, 4),
    )

    risk_flags = _generate_risk_flags(dscr_result, inp, effective_ltv)
    recommendation = _recommendation(dscr_result, risk_flags)
    confidence = _confidence_score(dscr_result, risk_flags)

    return UnderwritingReport(
        property_id=inp.property_id,
        dscr_result=dscr_result,
        risk_flags=risk_flags,
        recommendation=recommendation,
        underwriting_confidence=confidence,
    )


def _generate_risk_flags(
    r: DSCRResult, inp: UnderwritingInput, ltv: float
) -> list[RiskFlag]:
    flags: list[RiskFlag] = []

    if r.dscr_base < 1.0:
        flags.append(RiskFlag(flag_type="dscr_negative", severity="critical", message="DSCR below 1.0 — negative cash flow", value=r.dscr_base))
    elif r.dscr_base < 1.20:
        flags.append(RiskFlag(flag_type="dscr_thin", severity="warning", message="DSCR below 1.20 institutional threshold", value=r.dscr_base))

    if r.dscr_combined_stress < 1.0:
        flags.append(RiskFlag(flag_type="stress_dscr_negative", severity="critical", message="Combined stress DSCR below 1.0 — insolvent under shock", value=r.dscr_combined_stress))
    elif r.dscr_combined_stress < 1.05:
        flags.append(RiskFlag(flag_type="stress_dscr_thin", severity="warning", message="Combined stress DSCR below 1.05 conservative threshold", value=r.dscr_combined_stress))

    if ltv > 0.80:
        flags.append(RiskFlag(flag_type="high_ltv", severity="warning", message=f"LTV {ltv:.0%} exceeds 80% — limits lender options", value=ltv))

    if r.cash_on_cash_return < 0.05:
        flags.append(RiskFlag(flag_type="low_coc", severity="info", message=f"CoC return {r.cash_on_cash_return:.1%} below 5% target", value=r.cash_on_cash_return))

    if inp.rehab_cost_estimate / inp.purchase_price > 0.30:
        flags.append(RiskFlag(flag_type="heavy_rehab", severity="warning", message="Rehab cost exceeds 30% of purchase — execution risk elevated"))

    if r.cap_rate < 0.06:
        flags.append(RiskFlag(flag_type="low_cap_rate", severity="info", message=f"Cap rate {r.cap_rate:.1%} below 6% — compressed return", value=r.cap_rate))

    return flags


def _recommendation(result: DSCRResult, flags: list[RiskFlag]) -> str:
    critical = [f for f in flags if f.severity == "critical"]
    warnings = [f for f in flags if f.severity == "warning"]

    if critical:
        return "REJECT"
    if result.dscr_base >= 1.25 and result.dscr_combined_stress >= 1.10 and len(warnings) == 0:
        return "STRONG_BUY"
    if result.dscr_base >= 1.20:
        return "BUY"
    if result.dscr_base >= 1.10:
        return "CONDITIONAL"
    return "REJECT"


def _confidence_score(result: DSCRResult, flags: list[RiskFlag]) -> float:
    base = 0.70
    if result.dscr_base >= 1.25:
        base += 0.10
    if result.dscr_combined_stress >= 1.10:
        base += 0.10
    critical_penalty = sum(0.20 for f in flags if f.severity == "critical")
    warning_penalty = sum(0.05 for f in flags if f.severity == "warning")
    return max(0.0, min(1.0, base - critical_penalty - warning_penalty))
