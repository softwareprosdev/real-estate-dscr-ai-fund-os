"""
Competitive market intelligence tracker.

Computes investor saturation, institutional presence, and deal velocity
by ZIP code from aggregated listing + transaction data.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ZipMarketData:
    zip_code: str
    listing_velocity_30d: int = 0
    price_reduction_pct: float = 0.0
    avg_dom: float = 30.0
    wholesale_deal_count_30d: int = 0
    auction_participation_density: float = 0.0
    institutional_buyer_pct: float = 0.0
    flip_count_12m: int = 0
    rental_conversion_rate: float = 0.0
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ZipIntelligence:
    zip_code: str
    investor_saturation_index: float
    institutional_presence_score: float
    deal_velocity_score: float
    competition_risk: str
    summary: str


def compute_zip_intelligence(data: ZipMarketData) -> ZipIntelligence:
    velocity_score = min(1.0, data.listing_velocity_30d / 50)
    saturation = (
        0.30 * velocity_score
        + 0.25 * data.auction_participation_density
        + 0.25 * data.institutional_buyer_pct
        + 0.10 * min(1.0, data.wholesale_deal_count_30d / 20)
        + 0.10 * (1 - min(1.0, data.avg_dom / 90))
    )
    institutional_presence = (
        0.60 * data.institutional_buyer_pct
        + 0.40 * data.auction_participation_density
    )
    deal_velocity = (
        0.50 * velocity_score
        + 0.30 * min(1.0, data.flip_count_12m / 30)
        + 0.20 * data.rental_conversion_rate
    )

    if saturation >= 0.70:
        risk = "HIGH"
        summary = "Heavily contested ZIP — institutional buyers active, margins compressed"
    elif saturation >= 0.40:
        risk = "MEDIUM"
        summary = "Moderate competition — selectivity required on pricing"
    else:
        risk = "LOW"
        summary = "Under-served ZIP — opportunity for first-mover advantage"

    return ZipIntelligence(
        zip_code=data.zip_code,
        investor_saturation_index=round(saturation, 3),
        institutional_presence_score=round(institutional_presence, 3),
        deal_velocity_score=round(deal_velocity, 3),
        competition_risk=risk,
        summary=summary,
    )
