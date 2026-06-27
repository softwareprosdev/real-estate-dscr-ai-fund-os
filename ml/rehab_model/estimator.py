"""
Rehab cost estimator using XGBoost with feature engineering.

In production, this is trained on real contractor bids correlated with
property condition, age, and type. Here we provide a calibrated
rule-based baseline + XGBoost wrapper for training on real data.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from backend.shared_models.property import PropertyCondition, PropertyType


# Cost-per-sqft by condition and property type (USD, 2024 estimates)
CONDITION_BASE_CPSqFT: dict[str, float] = {
    PropertyCondition.EXCELLENT: 5.0,
    PropertyCondition.GOOD: 15.0,
    PropertyCondition.FAIR: 35.0,
    PropertyCondition.POOR: 60.0,
    PropertyCondition.DISTRESSED: 95.0,
}

PROPERTY_TYPE_MULTIPLIER: dict[str, float] = {
    PropertyType.SFR: 1.0,
    PropertyType.DUPLEX: 1.05,
    PropertyType.TRIPLEX: 1.08,
    PropertyType.FOURPLEX: 1.10,
    PropertyType.SMALL_MULTIFAMILY: 1.15,
}

AGE_SURCHARGE_PER_DECADE = 0.04


@dataclass
class RehabEstimate:
    property_id: str
    base_estimate: float
    low_estimate: float
    high_estimate: float
    confidence: float
    cost_per_sqft: float
    risk_flags: list[str]


def estimate_rehab(
    property_id: str,
    sqft: float,
    condition: str,
    property_type: str,
    year_built: int,
) -> RehabEstimate:
    base_cpsf = CONDITION_BASE_CPSqFT.get(condition, 35.0)
    type_mult = PROPERTY_TYPE_MULTIPLIER.get(property_type, 1.0)

    age = max(0, 2024 - year_built)
    decades_old = age / 10
    age_factor = 1.0 + (AGE_SURCHARGE_PER_DECADE * decades_old)

    effective_cpsf = base_cpsf * type_mult * age_factor

    # Older systems (electrical, plumbing, HVAC) add step costs at thresholds
    system_surcharge = 0.0
    flags = []
    if age > 50:
        system_surcharge += sqft * 8
        flags.append("50+ year old property: likely electrical/plumbing overhaul needed")
    if age > 30:
        system_surcharge += sqft * 3
        flags.append("30+ year old HVAC likely requires replacement")

    base_estimate = (effective_cpsf * sqft) + system_surcharge
    variance = 0.25 if condition in [PropertyCondition.FAIR, PropertyCondition.GOOD] else 0.40

    return RehabEstimate(
        property_id=property_id,
        base_estimate=round(base_estimate, 0),
        low_estimate=round(base_estimate * (1 - variance / 2), 0),
        high_estimate=round(base_estimate * (1 + variance), 0),
        confidence=0.75 if age < 30 else 0.60,
        cost_per_sqft=round(effective_cpsf, 2),
        risk_flags=flags,
    )


class RehabXGBoostModel:
    """
    Wrapper for XGBoost rehab model — trained on actual contractor bid data.
    Falls back to rule-based estimator if model not yet trained.
    """

    def __init__(self, model_path: str | None = None):
        self._model = None
        if model_path:
            self._load(model_path)

    def _load(self, path: str) -> None:
        try:
            import xgboost as xgb
            self._model = xgb.Booster()
            self._model.load_model(path)
        except Exception:
            self._model = None

    def predict(
        self,
        property_id: str,
        sqft: float,
        condition: str,
        property_type: str,
        year_built: int,
        zip_median_price: float = 200_000,
    ) -> RehabEstimate:
        if self._model is None:
            return estimate_rehab(property_id, sqft, condition, property_type, year_built)

        import xgboost as xgb
        features = np.array([[sqft, year_built, zip_median_price,
                               list(CONDITION_BASE_CPSqFT.keys()).index(condition),
                               list(PROPERTY_TYPE_MULTIPLIER.keys()).index(property_type)]])
        dmatrix = xgb.DMatrix(features)
        pred = float(self._model.predict(dmatrix)[0])

        rule_estimate = estimate_rehab(property_id, sqft, condition, property_type, year_built)
        return RehabEstimate(
            property_id=property_id,
            base_estimate=round(pred, 0),
            low_estimate=round(pred * 0.80, 0),
            high_estimate=round(pred * 1.30, 0),
            confidence=0.82,
            cost_per_sqft=round(pred / sqft, 2),
            risk_flags=rule_estimate.risk_flags,
        )
