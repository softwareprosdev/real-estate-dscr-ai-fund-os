"""
Real-world DSCR lender profiles calibrated to June 2025 market conditions.

Sources: Kiavi, Visio Financial, Deephaven, Lima One Capital, CoreVest (RCAP),
Angel Oak Mortgage, Civic Financial. Rates as of June 2025:
- 30yr fixed DSCR: 7.25%–9.25% (10yr Treasury ~4.3% + 300–500bps spread)
- 5/6 ARM DSCR: 6.75%–8.25%
- Bridge / hard money: 11%–13.5%

LTV: most DSCR lenders cap at 75–80% for SFR/1-4 unit.
DSCR mins vary: most DSCR-specific lenders allow ≥ 1.0; bank portfolio lenders require ≥ 1.25.
Min loan: $75k (Kiavi, Visio) to $250k (CoreVest portfolio product).
"""
from backend.shared_models.lender import LenderProfile, LenderType

LENDER_REGISTRY: list[LenderProfile] = [
    # Kiavi (formerly LendingHome) — volume DSCR lender, tech-first, fast close
    # Published guidelines Q2 2025: min 680 FICO, 1.0 DSCR, 80% LTV, $75k–$3M
    LenderProfile(
        lender_id="kiavi",
        lender_name="Kiavi (DSCR 30yr Fixed)",
        lender_type=LenderType.DSCR_SPECIALIST,
        dscr_min=1.00,
        dscr_stress_min=0.90,
        ltv_max=0.80,
        loan_min=75_000,
        loan_max=3_000_000,
        property_condition_min_score=0.40,
        zip_risk_sensitivity=0.45,
        property_age_sensitivity=0.35,
        loan_size_sensitivity=0.30,
        base_rate=0.0799,          # ~7.99% as of June 2025 for 1.0 DSCR / 75% LTV
        rate_spread_bps=75,         # Spread for lower DSCR / higher LTV
    ),
    # Visio Financial Services — DSCR-only lender, 1–4 unit residential
    # Published: 1.0 DSCR min, 80% LTV, $75k–$2M, 30yr and ARM products
    # Current 30yr rate: ~8.0–8.75% (mid June 2025)
    LenderProfile(
        lender_id="visio_30yr",
        lender_name="Visio Financial (30yr DSCR Fixed)",
        lender_type=LenderType.DSCR_SPECIALIST,
        dscr_min=1.00,
        dscr_stress_min=0.88,
        ltv_max=0.80,
        loan_min=75_000,
        loan_max=2_000_000,
        property_condition_min_score=0.45,
        zip_risk_sensitivity=0.50,
        property_age_sensitivity=0.40,
        loan_size_sensitivity=0.25,
        base_rate=0.0825,           # 8.25% base for standard DSCR profile
        rate_spread_bps=100,
    ),
    # CoreVest Finance (ReadyCap Commercial) — institutional DSCR, stricter but better rates
    # Single-asset product: $75k–$5M, 75% LTV, 1.20 DSCR min
    # Rate: ~7.25–7.75% for strong profiles (best rate in institutional DSCR segment)
    LenderProfile(
        lender_id="corevest",
        lender_name="CoreVest Finance (Institutional DSCR)",
        lender_type=LenderType.CONSERVATIVE_BANK,
        dscr_min=1.20,
        dscr_stress_min=1.10,
        ltv_max=0.75,
        loan_min=75_000,
        loan_max=5_000_000,
        property_condition_min_score=0.55,
        zip_risk_sensitivity=0.65,
        property_age_sensitivity=0.55,
        loan_size_sensitivity=0.25,
        base_rate=0.0749,           # 7.49% for 1.25+ DSCR, 70% LTV (best execution)
        rate_spread_bps=60,
    ),
    # Lima One Capital — RTL (Rental Transition Loan), DSCR permanent after rehab
    # Min 1.0 DSCR, 80% LTV, $75k–$3.5M; slightly higher rates than Kiavi
    # Known for accepting more property condition risk post-rehab
    LenderProfile(
        lender_id="lima_one",
        lender_name="Lima One Capital (Rental 30)",
        lender_type=LenderType.DSCR_SPECIALIST,
        dscr_min=1.00,
        dscr_stress_min=0.85,
        ltv_max=0.80,
        loan_min=75_000,
        loan_max=3_500_000,
        property_condition_min_score=0.35,   # More flexible on post-rehab condition
        zip_risk_sensitivity=0.40,
        property_age_sensitivity=0.30,
        loan_size_sensitivity=0.35,
        base_rate=0.0850,           # 8.50% base; Lima One prices slightly wider than Kiavi
        rate_spread_bps=125,
    ),
    # Deephaven Mortgage — non-QM / DSCR; requires ≥ 1.0 DSCR, 80% LTV
    # Popular with distressed/value-add because no income verification required
    # Rate: ~8.50–10.0% depending on LTV and DSCR
    LenderProfile(
        lender_id="deephaven",
        lender_name="Deephaven Mortgage (Non-QM DSCR)",
        lender_type=LenderType.DSCR_SPECIALIST,
        dscr_min=1.00,
        dscr_stress_min=0.85,
        ltv_max=0.80,
        loan_min=100_000,
        loan_max=2_500_000,
        property_condition_min_score=0.40,
        zip_risk_sensitivity=0.55,
        property_age_sensitivity=0.45,
        loan_size_sensitivity=0.40,
        base_rate=0.0875,
        rate_spread_bps=125,
    ),
    # Private / Hard Money Bridge — for distressed acquisitions pre-renovation
    # 12% interest-only, 12–18 month term, 65–70% LTV, points on origination
    # DSCR not the primary underwrite; ARV and exit strategy matters more
    LenderProfile(
        lender_id="private_bridge",
        lender_name="Private Hard Money Bridge Lender",
        lender_type=LenderType.PRIVATE_BRIDGE,
        dscr_min=1.00,             # Minimum post-stabilization DSCR for exit financing
        dscr_stress_min=0.80,
        ltv_max=0.70,              # Hard money: 65–70% LTV (of ARV or purchase, whichever lower)
        loan_min=50_000,
        loan_max=3_000_000,
        property_condition_min_score=0.10,   # Will lend on nearly any condition
        zip_risk_sensitivity=0.20,
        property_age_sensitivity=0.15,
        loan_size_sensitivity=0.50,
        base_rate=0.1200,          # 12% interest-only (current hard money market rate, June 2025)
        rate_spread_bps=200,        # Up to 14% for very high risk
    ),
    # Angel Oak Mortgage — non-QM, DSCR programs, slightly more conservative than Deephaven
    # Min 1.0 DSCR, 75–80% LTV, $100k–$3M
    LenderProfile(
        lender_id="angel_oak",
        lender_name="Angel Oak Mortgage (Non-QM DSCR)",
        lender_type=LenderType.DSCR_SPECIALIST,
        dscr_min=1.10,
        dscr_stress_min=0.95,
        ltv_max=0.75,
        loan_min=100_000,
        loan_max=3_000_000,
        property_condition_min_score=0.45,
        zip_risk_sensitivity=0.55,
        property_age_sensitivity=0.45,
        loan_size_sensitivity=0.30,
        base_rate=0.0899,
        rate_spread_bps=100,
    ),
    # Local Credit Union / Community Bank Portfolio Lender
    # Fills the sub-$75k loan gap that DSCR specialists won't touch.
    # Many regional credit unions and community banks in cash flow markets (Memphis, Cleveland,
    # Detroit, Birmingham) run in-house landlord loan programs with rates 8.5–10% and $25k min.
    # These are portfolio loans — held on balance sheet, more flexible on condition and
    # small loan sizes. Not securitized, so they trade rate for flexibility.
    LenderProfile(
        lender_id="local_portfolio_cu",
        lender_name="Local Credit Union / Community Bank Portfolio Loan",
        lender_type=LenderType.AGGRESSIVE_PORTFOLIO,
        dscr_min=1.10,
        dscr_stress_min=0.90,
        ltv_max=0.75,
        loan_min=25_000,           # Will do loans as small as $25k in cash flow markets
        loan_max=500_000,          # Max per property; portfolio limits apply
        property_condition_min_score=0.35,
        zip_risk_sensitivity=0.30,
        property_age_sensitivity=0.30,
        loan_size_sensitivity=0.10,  # Small loans are fine — they hold these in-house
        base_rate=0.0925,          # 9.25% for small-balance rental (typical CU/portfolio rate)
        rate_spread_bps=150,
    ),
]
