"""
Unit tests for DSCR underwriting engine.
All financial calculations must be deterministic and correct.
"""
import pytest
from core.underwriting_engine.engine import underwrite, _monthly_payment
from backend.shared_models.underwriting import UnderwritingInput


def make_standard_input(**overrides) -> UnderwritingInput:
    defaults = dict(
        property_id="TEST001",
        purchase_price=85_000,
        arv=115_000,
        estimated_monthly_rent=1_050,
        section_8_rent=1_150,
        rehab_cost_estimate=15_000,
        loan_rate=0.079,
        ltv=0.75,
        vacancy_rate=0.08,
        property_mgmt_rate=0.10,
        maintenance_rate=0.05,
        capex_rate=0.05,
    )
    defaults.update(overrides)
    return UnderwritingInput(**defaults)


def test_monthly_payment_accuracy():
    # $100k loan at 7.9% for 30 years = ~$727/mo
    payment = _monthly_payment(100_000, 0.079, 30)
    assert 720 <= payment <= 740, f"Expected ~$727, got {payment:.2f}"


def test_monthly_payment_zero_rate():
    payment = _monthly_payment(100_000, 0.0, 30)
    assert abs(payment - 100_000 / 360) < 0.01


def test_dscr_uses_section_8_when_higher():
    inp = make_standard_input()
    report = underwrite(inp)
    # Section 8 rent (1150) > market rent (1050), gross should use 1150
    assert report.dscr_result.gross_rent > inp.estimated_monthly_rent * 12


def test_dscr_base_positive_for_strong_deal():
    inp = make_standard_input(purchase_price=65_000, estimated_monthly_rent=1050, section_8_rent=1150)
    report = underwrite(inp)
    assert report.dscr_result.dscr_base > 1.20, "Strong deal should clear 1.20 DSCR"


def test_dscr_fails_for_overpriced_deal():
    inp = make_standard_input(purchase_price=500_000, estimated_monthly_rent=1050, section_8_rent=1100)
    report = underwrite(inp)
    assert report.dscr_result.dscr_base < 1.0, "Overpriced deal should fail DSCR"
    assert report.recommendation == "REJECT"


def test_stress_dscr_lower_than_base():
    inp = make_standard_input()
    report = underwrite(inp)
    r = report.dscr_result
    assert r.dscr_combined_stress <= r.dscr_base, "Combined stress must be <= base DSCR"
    assert r.dscr_stress_rate_plus_200bps <= r.dscr_base


def test_cash_on_cash_return_calculation():
    inp = make_standard_input()
    report = underwrite(inp)
    r = report.dscr_result
    # Sanity: annual CF / equity invested
    loan = inp.purchase_price * inp.ltv
    equity = (inp.purchase_price - loan) + inp.rehab_cost_estimate
    expected_coc = r.cash_flow_annual / equity
    assert abs(r.cash_on_cash_return - expected_coc) < 0.001


def test_noi_equals_egi_minus_opex():
    inp = make_standard_input()
    report = underwrite(inp)
    r = report.dscr_result
    computed_noi = r.effective_gross_income - r.operating_expenses
    assert abs(r.noi - computed_noi) < 1.0


def test_strong_deal_recommendation():
    inp = make_standard_input(purchase_price=55_000, estimated_monthly_rent=1050, section_8_rent=1150)
    report = underwrite(inp)
    assert report.recommendation in ("BUY", "STRONG_BUY")


def test_underwriting_confidence_range():
    inp = make_standard_input()
    report = underwrite(inp)
    assert 0.0 <= report.underwriting_confidence <= 1.0


def test_high_ltv_generates_risk_flag():
    inp = make_standard_input(ltv=0.85)
    report = underwrite(inp)
    flag_types = [f.flag_type for f in report.risk_flags]
    assert "high_ltv" in flag_types


def test_heavy_rehab_generates_flag():
    inp = make_standard_input(rehab_cost_estimate=40_000, purchase_price=85_000)
    report = underwrite(inp)
    flag_types = [f.flag_type for f in report.risk_flags]
    assert "heavy_rehab" in flag_types
