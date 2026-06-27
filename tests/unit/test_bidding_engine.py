"""
Unit tests for bidding engine.
"""
import pytest
from bidding_system.real_time_bidding_engine.engine import optimize_bid, calculate_max_allowable_bid


def test_max_bid_respects_dscr_constraint():
    max_bid = calculate_max_allowable_bid(
        property_id="TEST001",
        estimated_monthly_rent=1050,
        rehab_cost=15_000,
        target_dscr=1.20,
    )
    assert max_bid > 0
    # Max bid should be well below ARV for a $1050/mo property
    assert max_bid < 300_000


def test_overpriced_ask_bids_max_allowable():
    result = optimize_bid(
        property_id="TEST001",
        source="auction",
        ask_price=250_000,
        estimated_monthly_rent=1050,
        rehab_cost=15_000,
        arv=115_000,
    )
    assert result.recommended_bid <= result.max_allowable_bid
    assert result.bid_strategy == "max_dscr_bid"


def test_high_competition_applies_discount():
    result = optimize_bid(
        property_id="TEST002",
        source="wholesale",
        ask_price=85_000,
        estimated_monthly_rent=1050,
        rehab_cost=15_000,
        arv=115_000,
        competition_saturation=0.85,
        days_on_market=10,
    )
    assert result.recommended_bid <= result.current_ask * 0.95
    assert result.bid_strategy == "competitive_discount"


def test_motivated_seller_applies_larger_discount():
    result = optimize_bid(
        property_id="TEST003",
        source="mls",
        ask_price=85_000,
        estimated_monthly_rent=1050,
        rehab_cost=15_000,
        arv=115_000,
        competition_saturation=0.30,
        days_on_market=120,
    )
    assert result.recommended_bid <= result.current_ask * 0.95
    assert result.bid_strategy == "motivated_seller_discount"


def test_win_probability_in_range():
    result = optimize_bid(
        property_id="TEST004",
        source="auction",
        ask_price=85_000,
        estimated_monthly_rent=1050,
        rehab_cost=15_000,
        arv=115_000,
    )
    assert 0.0 <= result.win_probability <= 1.0


def test_bid_result_has_all_fields():
    result = optimize_bid(
        property_id="TEST005",
        source="wholesale",
        ask_price=85_000,
        estimated_monthly_rent=1050,
        rehab_cost=15_000,
        arv=115_000,
    )
    assert result.property_id == "TEST005"
    assert result.max_allowable_bid > 0
    assert len(result.reasoning) > 0
