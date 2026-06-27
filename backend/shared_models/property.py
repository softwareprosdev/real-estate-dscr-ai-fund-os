from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class PropertyCondition(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DISTRESSED = "distressed"


class PropertyType(str, Enum):
    SFR = "sfr"
    DUPLEX = "duplex"
    TRIPLEX = "triplex"
    FOURPLEX = "fourplex"
    SMALL_MULTIFAMILY = "small_multifamily"


class DataSource(str, Enum):
    MLS = "mls"
    WHOLESALE = "wholesale"
    AUCTION = "auction"
    OFF_MARKET = "off_market"
    EMAIL = "email"


class PropertySchema(BaseModel):
    property_id: str
    address: str
    city: str
    state: str
    zip_code: str
    property_type: PropertyType
    sqft: float
    year_built: int
    bedrooms: int
    bathrooms: float
    lot_size_sqft: Optional[float] = None
    condition: PropertyCondition
    condition_score: float = Field(ge=0.0, le=1.0)

    list_price: float
    arv: Optional[float] = None
    estimated_rent: Optional[float] = None
    section_8_rent: Optional[float] = None

    source: DataSource
    source_listing_id: Optional[str] = None
    days_on_market: Optional[int] = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("condition_score")
    @classmethod
    def score_from_condition(cls, v: float, info) -> float:
        return v

    class Config:
        use_enum_values = True


class PropertyEnrichment(BaseModel):
    property_id: str
    zip_median_rent: Optional[float] = None
    zip_vacancy_rate: Optional[float] = None
    zip_rent_growth_yoy: Optional[float] = None
    zip_investor_activity_index: Optional[float] = None
    zip_liquidity_index: Optional[float] = None
    zip_institutional_presence: Optional[float] = None
    walk_score: Optional[int] = None
    flood_zone: Optional[str] = None
    crime_index: Optional[float] = None
    school_rating: Optional[float] = None
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
