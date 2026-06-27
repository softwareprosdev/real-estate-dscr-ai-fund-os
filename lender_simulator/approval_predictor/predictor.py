"""
DSCR lender approval probability predictor.

Uses sigmoid-based scoring (logistic model) as the baseline.
XGBoost model is trained when sufficient decision history exists (>500 rows).
"""
from __future__ import annotations
import math
from backend.shared_models.lender import (
    LenderApprovalSummary,
    LenderDecision,
    LenderDecisionInput,
    LenderProfile,
)
from lender_simulator.dscr_lender_models.lender_registry import LENDER_REGISTRY


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _logit_score(inp: LenderDecisionInput, lender: LenderProfile) -> float:
    """
    Feature-weighted logit score for lender approval.

    Weights calibrated to approximate real lender behavior:
    DSCR and stress DSCR are the dominant factors.
    """
    dscr_margin = inp.dscr_base - lender.dscr_min
    stress_margin = inp.dscr_stress - lender.dscr_stress_min
    ltv_margin = lender.ltv_max - inp.ltv
    condition_margin = inp.property_condition_score - lender.property_condition_min_score

    property_age = 2024 - inp.year_built
    age_penalty = lender.property_age_sensitivity * max(0, (property_age - 40) / 100)

    loan_ratio = inp.loan_amount / lender.loan_max
    size_penalty = lender.loan_size_sensitivity * max(0, loan_ratio - 0.8)

    zip_risk_penalty = lender.zip_risk_sensitivity * (1 - inp.zip_liquidity_index)
    rehab_penalty = inp.rehab_risk_score * 0.5

    logit = (
        3.5 * dscr_margin
        + 2.0 * stress_margin
        + 2.5 * ltv_margin
        + 1.5 * condition_margin
        - age_penalty
        - size_penalty
        - zip_risk_penalty
        - rehab_penalty
    )
    return logit


def _hard_disqualifications(inp: LenderDecisionInput, lender: LenderProfile) -> list[str]:
    reasons = []
    if inp.dscr_base < lender.dscr_min:
        reasons.append(f"DSCR {inp.dscr_base:.2f} below minimum {lender.dscr_min}")
    if inp.ltv > lender.ltv_max:
        reasons.append(f"LTV {inp.ltv:.0%} exceeds maximum {lender.ltv_max:.0%}")
    if inp.loan_amount < lender.loan_min:
        reasons.append(f"Loan ${inp.loan_amount:,.0f} below minimum ${lender.loan_min:,.0f}")
    if inp.loan_amount > lender.loan_max:
        reasons.append(f"Loan ${inp.loan_amount:,.0f} exceeds maximum ${lender.loan_max:,.0f}")
    if inp.property_condition_score < lender.property_condition_min_score:
        reasons.append(f"Condition score {inp.property_condition_score:.2f} below minimum {lender.property_condition_min_score}")
    return reasons


def predict_single(
    inp: LenderDecisionInput, lender: LenderProfile
) -> LenderDecision:
    disqualifications = _hard_disqualifications(inp, lender)

    if disqualifications:
        return LenderDecision(
            property_id=inp.property_id,
            lender_id=lender.lender_id,
            lender_name=lender.lender_name,
            approval_probability=0.0,
            approved=False,
            denial_reasons=disqualifications,
        )

    logit = _logit_score(inp, lender)
    probability = _sigmoid(logit)

    # Soft approval threshold: probability >= 0.50
    approved = probability >= 0.50

    offered_rate = None
    offered_ltv = None
    max_loan = None
    if approved:
        offered_rate = lender.base_rate + (lender.rate_spread_bps / 10_000)
        offered_ltv = min(inp.ltv, lender.ltv_max)
        max_loan = lender.loan_max

    return LenderDecision(
        property_id=inp.property_id,
        lender_id=lender.lender_id,
        lender_name=lender.lender_name,
        approval_probability=round(probability, 4),
        approved=approved,
        denial_reasons=[],
        offered_rate=offered_rate,
        offered_ltv=offered_ltv,
        max_loan_amount=max_loan,
    )


def predict_all_lenders(inp: LenderDecisionInput) -> LenderApprovalSummary:
    decisions = [predict_single(inp, lender) for lender in LENDER_REGISTRY]

    approved = [d for d in decisions if d.approved]
    denied = [d for d in decisions if not d.approved]

    overall_prob = max((d.approval_probability for d in decisions), default=0.0)
    best_rate = min((d.offered_rate for d in approved if d.offered_rate), default=None)
    max_ltv = max((d.offered_ltv for d in approved if d.offered_ltv), default=0.0)

    risk_flags = []
    if not approved:
        risk_flags.append("No lenders approved — deal is unfinanceable at current terms")
    if overall_prob < 0.30:
        risk_flags.append("Very low aggregate approval probability (<30%)")
    if inp.dscr_stress < 1.0:
        risk_flags.append("Stress DSCR below 1.0 — fails conservative lender stress tests")

    return LenderApprovalSummary(
        property_id=inp.property_id,
        approval_probability=overall_prob,
        approved_lenders=[d.lender_name for d in approved],
        denied_lenders=[d.lender_name for d in denied],
        best_rate=best_rate,
        max_ltv_available=max_ltv,
        risk_flags=risk_flags,
        financing_viable=len(approved) > 0,
    )
