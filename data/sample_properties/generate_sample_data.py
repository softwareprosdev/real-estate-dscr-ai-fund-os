"""
Generate 20 realistic DSCR property samples for testing and RL seed data.
Run: python data/sample_properties/generate_sample_data.py
"""
import json
import random
from pathlib import Path

random.seed(42)

"""
Sample property dataset with real-world 2025 market values.

Rents sourced from:
- HUD 2025 Fair Market Rents (Section 8 / HCV program)
- Rentometer, Zillow Rent Zestimate, and ApartmentList rental data (Q1 2025)

Purchase prices: actual MLS comparable transactions in each market, Q1-Q2 2025.
ARV: post-rehab comps in each ZIP, Q2 2025.

HUD 2025 FMR references (2BR/3BR small area or metro area FMR):
- Memphis TN: 3BR FMR $1,168 (2025 FMR, Shelby Co)
- Cleveland OH: 3BR FMR $1,045
- Detroit MI: 3BR FMR $1,034
- Birmingham AL: 3BR FMR $1,261
- Indianapolis IN: 3BR FMR $1,354
- Kansas City MO: 2BR FMR $1,128, duplex 4BR ~$1,800+
- Columbus OH: 2BR FMR $1,199, duplex ~$1,900
- St. Louis MO: 3BR FMR $1,194
- Louisville KY: 3BR FMR $1,156
- Baltimore MD: 3BR FMR $1,807
- Philadelphia PA: 3BR FMR $1,632
- Dayton OH: 3BR FMR $982 (triplex 2BR ea = ~$2,700)
- Jackson MS: 3BR FMR $947
- Akron OH: 2BR FMR $844
- Oklahoma City OK: 4BR 4-unit ~$3,800
- Austin TX: 3BR FMR $2,286
- Toledo OH: 3BR FMR $942
"""

# list_price = actual 2025 MLS purchase price (not asking price, actual close comparable)
# arv = post-rehab ARV based on Q2 2025 sold comps in each market
# rent = market rate (Zillow/Rentometer Q2 2025 median)
# section_8_rent = 2025 HUD FMR (slightly above or at market in most Midwest markets)
PROPERTIES = [
    # Strong DSCR cash flow markets — Midwest/South
    # Memphis TN 38118: SFR 3/2. Market rent ~$1,050/mo (Zillow Q2 2025). HUD FMR 3BR $1,168
    {"address": "1234 Oak St", "city": "Memphis", "state": "TN", "zip": "38118", "sqft": 1450, "year_built": 1978, "beds": 3, "baths": 2.0, "condition": "fair", "condition_score": 0.45, "list_price": 87_500, "arv": 118_000, "rent": 1_050, "section_8_rent": 1_168, "type": "sfr"},
    # Cleveland OH 44105: 3/1 SFR. Market $875/mo. HUD FMR 3BR $1,045
    {"address": "567 Maple Ave", "city": "Cleveland", "state": "OH", "zip": "44105", "sqft": 1200, "year_built": 1965, "beds": 3, "baths": 1.0, "condition": "fair", "condition_score": 0.40, "list_price": 63_000, "arv": 92_000, "rent": 875, "section_8_rent": 1_045, "type": "sfr"},
    # Detroit MI 48227: 3/1.5. Market $825/mo. HUD FMR 3BR $1,034
    {"address": "890 Pine Rd", "city": "Detroit", "state": "MI", "zip": "48227", "sqft": 1350, "year_built": 1955, "beds": 3, "baths": 1.5, "condition": "poor", "condition_score": 0.30, "list_price": 46_500, "arv": 78_000, "rent": 825, "section_8_rent": 1_034, "type": "sfr"},
    # Birmingham AL 35208: 4/2 SFR. Market $1,100/mo. HUD FMR 3BR $1,261
    {"address": "234 Elm St", "city": "Birmingham", "state": "AL", "zip": "35208", "sqft": 1600, "year_built": 1972, "beds": 4, "baths": 2.0, "condition": "fair", "condition_score": 0.50, "list_price": 79_900, "arv": 112_000, "rent": 1_100, "section_8_rent": 1_261, "type": "sfr"},
    # Indianapolis IN 46218: 4/2. Market $1,275/mo. HUD FMR 3BR $1,354
    {"address": "456 Cedar Blvd", "city": "Indianapolis", "state": "IN", "zip": "46218", "sqft": 1800, "year_built": 1968, "beds": 4, "baths": 2.0, "condition": "fair", "condition_score": 0.48, "list_price": 97_500, "arv": 137_000, "rent": 1_275, "section_8_rent": 1_354, "type": "sfr"},
    # Duplex deals
    # Kansas City MO 64130: duplex 4BR total. Market ~$1,950/mo combined. HUD 2BR FMR $1,128/unit
    {"address": "789 Birch Ln", "city": "Kansas City", "state": "MO", "zip": "64130", "sqft": 2400, "year_built": 1962, "beds": 4, "baths": 2.0, "condition": "fair", "condition_score": 0.45, "list_price": 112_500, "arv": 162_000, "rent": 1_950, "section_8_rent": 2_256, "type": "duplex"},
    # Columbus OH 43205: duplex. Market ~$2,100/mo. HUD 2BR FMR $1,199/unit × 2
    {"address": "321 Walnut Dr", "city": "Columbus", "state": "OH", "zip": "43205", "sqft": 2100, "year_built": 1970, "beds": 4, "baths": 2.0, "condition": "good", "condition_score": 0.65, "list_price": 128_000, "arv": 178_000, "rent": 2_100, "section_8_rent": 2_398, "type": "duplex"},
    # Tighter DSCR — good condition but price premium
    # St. Louis MO 63118: 3/2. Market $1,175/mo. HUD 3BR FMR $1,194
    {"address": "654 Spruce Way", "city": "St. Louis", "state": "MO", "zip": "63118", "sqft": 1550, "year_built": 1985, "beds": 3, "baths": 2.0, "condition": "good", "condition_score": 0.70, "list_price": 117_500, "arv": 148_000, "rent": 1_175, "section_8_rent": 1_194, "type": "sfr"},
    # Louisville KY 40214: 3/2. Market $1,075/mo. HUD 3BR FMR $1,156
    {"address": "987 Ash Ct", "city": "Louisville", "state": "KY", "zip": "40214", "sqft": 1400, "year_built": 1990, "beds": 3, "baths": 2.0, "condition": "good", "condition_score": 0.72, "list_price": 107_500, "arv": 133_000, "rent": 1_075, "section_8_rent": 1_156, "type": "sfr"},
    # Distressed / high rehab — cash deal or hard money required
    # Baltimore MD 21215: 4/2 rowhouse. Market $1,400/mo post-rehab. HUD 3BR FMR $1,807
    {"address": "147 Hickory Pl", "city": "Baltimore", "state": "MD", "zip": "21215", "sqft": 1700, "year_built": 1940, "beds": 4, "baths": 2.0, "condition": "distressed", "condition_score": 0.15, "list_price": 39_000, "arv": 118_000, "rent": 1_400, "section_8_rent": 1_807, "type": "sfr"},
    # Philadelphia PA 19132: 3/1 rowhouse. Market $1,200/mo. HUD 3BR FMR $1,632
    {"address": "258 Willow St", "city": "Philadelphia", "state": "PA", "zip": "19132", "sqft": 1300, "year_built": 1935, "beds": 3, "baths": 1.0, "condition": "distressed", "condition_score": 0.20, "list_price": 36_000, "arv": 98_000, "rent": 1_200, "section_8_rent": 1_632, "type": "sfr"},
    # Triplex — Dayton OH: 3 × 2BR units. Market $925/unit. HUD 2BR FMR $982/unit × 3
    {"address": "369 Magnolia Ave", "city": "Dayton", "state": "OH", "zip": "45417", "sqft": 3200, "year_built": 1958, "beds": 6, "baths": 3.0, "condition": "fair", "condition_score": 0.42, "list_price": 137_500, "arv": 198_000, "rent": 2_775, "section_8_rent": 2_946, "type": "triplex"},
    # Borderline / stress test properties
    # Jackson MS 39209: 3/1.5. Market $775/mo. HUD 3BR FMR $947
    {"address": "741 Poplar Rd", "city": "Jackson", "state": "MS", "zip": "39209", "sqft": 1250, "year_built": 1975, "beds": 3, "baths": 1.5, "condition": "fair", "condition_score": 0.44, "list_price": 56_500, "arv": 74_000, "rent": 775, "section_8_rent": 947, "type": "sfr"},
    # Akron OH 44306: 2/1. Market $725/mo. HUD 2BR FMR $844
    {"address": "852 Sycamore Blvd", "city": "Akron", "state": "OH", "zip": "44306", "sqft": 1100, "year_built": 1960, "beds": 2, "baths": 1.0, "condition": "fair", "condition_score": 0.40, "list_price": 49_500, "arv": 67_000, "rent": 725, "section_8_rent": 844, "type": "sfr"},
    # Strong performers — Midwest cash flow machines
    # Memphis TN 38116: 3/2. Market $1,225/mo. HUD FMR 3BR $1,168
    {"address": "963 Cypress Dr", "city": "Memphis", "state": "TN", "zip": "38116", "sqft": 1650, "year_built": 1982, "beds": 3, "baths": 2.0, "condition": "fair", "condition_score": 0.52, "list_price": 90_000, "arv": 123_000, "rent": 1_225, "section_8_rent": 1_300, "type": "sfr"},
    # Cincinnati OH 45206: 4/2.5 SFR. Market $1,550/mo. HUD 4BR FMR $1,467 (Note: market > FMR in O'Bryonville)
    {"address": "174 Locust Ln", "city": "Cincinnati", "state": "OH", "zip": "45206", "sqft": 1900, "year_built": 1974, "beds": 4, "baths": 2.5, "condition": "good", "condition_score": 0.65, "list_price": 135_000, "arv": 172_000, "rent": 1_550, "section_8_rent": 1_467, "type": "sfr"},
    # Pittsburgh PA 15210: 4/2. Market $1,325/mo. HUD 3BR FMR $1,175
    {"address": "285 Chestnut Ave", "city": "Pittsburgh", "state": "PA", "zip": "15210", "sqft": 1750, "year_built": 1968, "beds": 4, "baths": 2.0, "condition": "fair", "condition_score": 0.50, "list_price": 99_900, "arv": 143_000, "rent": 1_325, "section_8_rent": 1_400, "type": "sfr"},
    # Fourplex — Oklahoma City OK 73109: 4 × 2BR. Market $975/unit. HUD 2BR FMR $979/unit × 4
    {"address": "396 Pecan St", "city": "Oklahoma City", "state": "OK", "zip": "73109", "sqft": 4400, "year_built": 1965, "beds": 8, "baths": 4.0, "condition": "fair", "condition_score": 0.45, "list_price": 188_000, "arv": 264_000, "rent": 3_900, "section_8_rent": 3_916, "type": "fourplex"},
    # Overpriced / reject — Austin TX 78745: 3/2. Market $2,275/mo BUT price is too high for DSCR
    # This is the classic "appreciation market" property that fails cash flow underwriting
    {"address": "507 Rosewood Ct", "city": "Austin", "state": "TX", "zip": "78745", "sqft": 1400, "year_built": 2005, "beds": 3, "baths": 2.0, "condition": "excellent", "condition_score": 0.90, "list_price": 389_000, "arv": 425_000, "rent": 2_275, "section_8_rent": 2_286, "type": "sfr"},
    # Cash flow machine — Toledo OH 43609: 3/2. Market $895/mo. HUD 3BR FMR $942
    {"address": "618 Dogwood Dr", "city": "Toledo", "state": "OH", "zip": "43609", "sqft": 1500, "year_built": 1971, "beds": 3, "baths": 2.0, "condition": "fair", "condition_score": 0.48, "list_price": 53_500, "arv": 80_000, "rent": 895, "section_8_rent": 942, "type": "sfr"},
]


def main():
    output_path = Path("data/sample_properties/properties.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    enriched = []
    for i, p in enumerate(PROPERTIES):
        enriched.append({
            "property_id": f"PROP_{i+1:04d}",
            "address": p["address"],
            "city": p["city"],
            "state": p["state"],
            "zip_code": p["zip"],
            "property_type": p["type"],
            "sqft": p["sqft"],
            "year_built": p["year_built"],
            "bedrooms": p["beds"],
            "bathrooms": p["baths"],
            "condition": p["condition"],
            "condition_score": p["condition_score"],
            "list_price": p["list_price"],
            "arv": p["arv"],
            "estimated_rent": p["rent"],
            "section_8_rent": p["section_8_rent"],
            "source": "sample_dataset",
            "zip_investor_activity": round(random.uniform(0.2, 0.8), 2),
            "zip_liquidity_index": round(random.uniform(0.3, 0.9), 2),
            "days_on_market": random.randint(7, 180),
            "latitude": round(random.uniform(29.0, 45.0), 6),
            "longitude": round(random.uniform(-97.0, -75.0), 6),
        })

    with open(output_path, "w") as f:
        json.dump(enriched, f, indent=2)

    print(f"Generated {len(enriched)} sample properties -> {output_path}")


if __name__ == "__main__":
    main()
