"""
End-to-end demo: underwrite all 20 sample properties and print results.
Run: python scripts/run_full_analysis.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.underwriting_engine.engine import underwrite
from backend.shared_models.underwriting import UnderwritingInput
from lender_simulator.approval_predictor.predictor import predict_all_lenders
from backend.shared_models.lender import LenderDecisionInput
from ml.rehab_model.estimator import estimate_rehab
from ai_agent.decision_engine.engine import decide, MarketContext, PortfolioConstraints
from bidding_system.real_time_bidding_engine.engine import optimize_bid


def main():
    data_path = Path("data/sample_properties/properties.json")
    if not data_path.exists():
        print("Generating sample data first...")
        import subprocess
        subprocess.run([sys.executable, "data/sample_properties/generate_sample_data.py"])

    with open(data_path) as f:
        properties = json.load(f)

    print(f"\n{'='*80}")
    print(f"DSCR AI FUND OS — Full Portfolio Analysis ({len(properties)} properties)")
    print(f"{'='*80}\n")

    decisions = {"BUY": 0, "STRONG_BUY": 0, "CONDITIONAL": 0, "REJECT": 0}

    for prop in properties:
        pid = prop["property_id"]
        price = prop["list_price"]
        rent = prop["section_8_rent"] or prop["estimated_rent"]

        uw_inp = UnderwritingInput(
            property_id=pid,
            purchase_price=price,
            arv=prop["arv"],
            estimated_monthly_rent=prop["estimated_rent"],
            section_8_rent=prop["section_8_rent"],
            rehab_cost_estimate=0,
            loan_rate=0.079,
            ltv=0.75,
        )
        report = underwrite(uw_inp)

        rehab = estimate_rehab(
            property_id=pid,
            sqft=prop["sqft"],
            condition=prop["condition"],
            property_type=prop["property_type"],
            year_built=prop["year_built"],
        )

        lender_inp = LenderDecisionInput(
            property_id=pid,
            lender_id="all",
            dscr_base=report.dscr_result.dscr_base,
            dscr_stress=report.dscr_result.dscr_combined_stress,
            ltv=0.75,
            loan_amount=price * 0.75,
            property_condition_score=prop["condition_score"],
            zip_code=prop["zip_code"],
            zip_liquidity_index=prop.get("zip_liquidity_index", 0.60),
            rehab_risk_score=min(1.0, rehab.base_estimate / price),
            year_built=prop["year_built"],
        )
        lender = predict_all_lenders(lender_inp)

        market = MarketContext(
            zip_investor_activity=prop.get("zip_investor_activity", 0.50),
            zip_liquidity_index=prop.get("zip_liquidity_index", 0.60),
            days_on_market=prop.get("days_on_market", 45),
            competition_saturation=prop.get("zip_investor_activity", 0.50),
            macro_regime="expansion",
        )
        constraints = PortfolioConstraints(available_cash=2_000_000)

        decision = decide(
            underwriting=report,
            lender_summary=lender,
            rehab=rehab,
            market=market,
            constraints=constraints,
            zip_code=prop["zip_code"],
            state=prop["state"],
        )

        bid = optimize_bid(
            property_id=pid,
            source="mls",
            ask_price=price,
            estimated_monthly_rent=rent,
            rehab_cost=rehab.base_estimate,
            arv=prop["arv"],
            competition_saturation=prop.get("zip_investor_activity", 0.50),
            days_on_market=prop.get("days_on_market", 45),
        )

        decisions[decision.decision] = decisions.get(decision.decision, 0) + 1

        color = "\033[92m" if decision.decision in ("BUY", "STRONG_BUY") else "\033[93m" if decision.decision == "CONDITIONAL" else "\033[91m"
        reset = "\033[0m"

        print(f"{color}[{decision.decision:12s}]{reset} {pid} | {prop['address']}, {prop['city']} | "
              f"Ask ${price:>8,.0f} | DSCR {report.dscr_result.dscr_base:.3f} | "
              f"CoC {report.dscr_result.cash_on_cash_return:.1%} | "
              f"Lender {lender.approval_probability:.0%} | "
              f"Bid ${bid.recommended_bid:>8,.0f} | "
              f"Confidence {decision.confidence:.0%}")

    print(f"\n{'='*80}")
    print("PORTFOLIO FILTER SUMMARY")
    print(f"  BUY/STRONG_BUY : {decisions.get('BUY', 0) + decisions.get('STRONG_BUY', 0)}")
    print(f"  CONDITIONAL    : {decisions.get('CONDITIONAL', 0)}")
    print(f"  REJECT         : {decisions.get('REJECT', 0)}")
    print(f"  Filter rate    : {decisions.get('REJECT', 0) / len(properties):.0%} rejected")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
