"""
Synthetic deal generator for RL training.

Generates realistic DSCR property deals with correlated features —
not random noise. Key correlations:
- Lower price → higher yield (Midwest cash flow markets)
- Higher condition score → lower rehab risk → higher lender approval
- High competition ZIP → lower returns
"""
from __future__ import annotations
import random
import numpy as np
from backend.shared_models.rl_schema import RLState


class SyntheticDealGenerator:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.np_rng = np.random.RandomState(seed)

    def next(self) -> dict:
        condition_score = self.rng.uniform(0.15, 0.85)
        purchase_price = self.rng.uniform(35_000, 250_000)

        # Rent yield inversely correlated with price (Midwest cash flow dynamics)
        base_rent_ratio = self.np_rng.normal(0.014, 0.003)
        monthly_rent = max(600, purchase_price * base_rent_ratio)

        ltv = self.rng.uniform(0.65, 0.80)
        loan_amount = purchase_price * ltv
        loan_rate = self.rng.uniform(0.072, 0.092)

        from core.underwriting_engine.engine import underwrite, _monthly_payment
        from backend.shared_models.underwriting import UnderwritingInput

        rehab = max(0, (1 - condition_score) * purchase_price * 0.30)
        inp = UnderwritingInput(
            property_id="RL_SIM",
            purchase_price=purchase_price,
            arv=purchase_price * self.rng.uniform(1.1, 1.5),
            estimated_monthly_rent=monthly_rent,
            rehab_cost_estimate=rehab,
            loan_rate=loan_rate,
            ltv=ltv,
            vacancy_rate=self.rng.uniform(0.05, 0.15),
        )

        try:
            report = underwrite(inp)
            r = report.dscr_result
        except Exception:
            return self.next()

        zip_investor = self.rng.uniform(0.10, 0.85)
        zip_liquidity = self.rng.uniform(0.30, 0.90)

        from lender_simulator.approval_predictor.predictor import predict_all_lenders
        from backend.shared_models.lender import LenderDecisionInput

        lender_inp = LenderDecisionInput(
            property_id="RL_SIM",
            lender_id="all",
            dscr_base=r.dscr_base,
            dscr_stress=r.dscr_combined_stress,
            ltv=ltv,
            loan_amount=loan_amount,
            property_condition_score=condition_score,
            zip_code="00000",
            zip_liquidity_index=zip_liquidity,
            rehab_risk_score=min(1.0, rehab / purchase_price),
            year_built=self.rng.randint(1940, 2005),
        )
        lender_summary = predict_all_lenders(lender_inp)

        state_vector = [
            inp.sqft if hasattr(inp, 'sqft') else 1400 / 10000,
            1978 / 2024,
            condition_score,
            3 / 10, 2.0 / 5,
            purchase_price / 1_000_000,
            r.dscr_base,
            r.dscr_combined_stress,
            r.noi / 100_000,
            ltv,
            r.cap_rate,
            r.cash_on_cash_return,
            r.irr_5yr_estimate,
            zip_investor,
            self.rng.uniform(-0.02, 0.06),
            self.rng.uniform(0.04, 0.14),
            zip_liquidity,
            self.rng.uniform(0.0, 0.8),
            self.rng.randint(7, 180) / 365,
            lender_summary.approval_probability,
            lender_summary.max_ltv_available,
            lender_summary.best_rate or 0.085,
            len(lender_summary.approved_lenders) / 10,
            float(lender_summary.financing_viable),
            2_000_000 / 10_000_000,
            0.0,
            0 / 100,
            1.25,
            0.20,
            0.0,
        ]

        return {
            "property_id": f"RL_{id(self)}",
            "purchase_price": purchase_price,
            "monthly_cash_flow": r.cash_flow_monthly,
            "dscr_base": r.dscr_base,
            "dscr_stress": r.dscr_combined_stress,
            "noi": r.noi,
            "ltv": ltv,
            "cap_rate": r.cap_rate,
            "irr_estimate": r.irr_5yr_estimate,
            "lender_approval_probability": lender_summary.approval_probability,
            "financing_viable": lender_summary.financing_viable,
            "zip_code": "00000",
            "state_vector": state_vector,
        }
