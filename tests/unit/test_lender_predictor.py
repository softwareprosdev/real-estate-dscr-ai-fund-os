"""
Unit tests for lender approval predictor.
"""
import pytest
from backend.shared_models.lender import LenderDecisionInput
from lender_simulator.approval_predictor.predictor import predict_all_lenders, predict_single
from lender_simulator.dscr_lender_models.lender_registry import LENDER_REGISTRY


def make_lender_input(**overrides) -> LenderDecisionInput:
    defaults = dict(
        property_id="TEST001",
        lender_id="test_lender",
        dscr_base=1.35,
        dscr_stress=1.15,
        ltv=0.72,
        loan_amount=63_750,
        property_condition_score=0.55,
        zip_code="38118",
        zip_liquidity_index=0.65,
        rehab_risk_score=0.20,
        year_built=1978,
    )
    defaults.update(overrides)
    return LenderDecisionInput(**defaults)


def test_all_lenders_returns_summary():
    inp = make_lender_input()
    summary = predict_all_lenders(inp)
    assert summary.property_id == "TEST001"
    assert 0.0 <= summary.approval_probability <= 1.0
    assert isinstance(summary.approved_lenders, list)
    assert isinstance(summary.denied_lenders, list)


def test_strong_deal_gets_approvals():
    inp = make_lender_input(dscr_base=1.40, dscr_stress=1.20, ltv=0.70, property_condition_score=0.70)
    summary = predict_all_lenders(inp)
    assert summary.financing_viable, "Strong deal should have at least one approved lender"
    assert len(summary.approved_lenders) >= 2


def test_below_minimum_dscr_hard_rejected():
    conservative = LENDER_REGISTRY[0]
    inp = make_lender_input(dscr_base=conservative.dscr_min - 0.10)
    decision = predict_single(inp, conservative)
    assert decision.approved is False
    assert decision.approval_probability == 0.0
    assert len(decision.denial_reasons) > 0


def test_excessive_ltv_hard_rejected():
    lender = LENDER_REGISTRY[0]  # 0.70 max LTV
    inp = make_lender_input(ltv=0.85)
    decision = predict_single(inp, lender)
    assert decision.approved is False


def test_distressed_property_rejected_by_conservative():
    conservative = LENDER_REGISTRY[0]
    inp = make_lender_input(property_condition_score=0.10)
    decision = predict_single(inp, conservative)
    assert decision.approved is False


def test_unfinanceable_deal_has_no_approved_lenders():
    inp = make_lender_input(dscr_base=0.80, dscr_stress=0.70, ltv=0.90)
    summary = predict_all_lenders(inp)
    assert len(summary.approved_lenders) == 0
    assert not summary.financing_viable


def test_approved_lender_has_rate():
    inp = make_lender_input(dscr_base=1.45, dscr_stress=1.25, ltv=0.65, property_condition_score=0.80)
    summary = predict_all_lenders(inp)
    if summary.financing_viable:
        assert summary.best_rate is not None
        assert summary.best_rate > 0.05


def test_lender_count_in_registry():
    assert len(LENDER_REGISTRY) >= 4, "Must have at least 4 lender profiles"


def test_probability_increases_with_better_dscr():
    lender = LENDER_REGISTRY[1]
    weak = predict_single(make_lender_input(dscr_base=1.22), lender)
    strong = predict_single(make_lender_input(dscr_base=1.50), lender)
    assert strong.approval_probability >= weak.approval_probability
