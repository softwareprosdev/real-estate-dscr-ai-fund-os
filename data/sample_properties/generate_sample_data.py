"""
Generate 20 realistic DSCR property samples for testing and RL seed data.
Run: python data/sample_properties/generate_sample_data.py
"""
import json
import random
from pathlib import Path

random.seed(42)

PROPERTIES = [
    # Strong DSCR deals
    {"address": "1234 Oak St", "city": "Memphis", "state": "TN", "zip": "38118", "sqft": 1450, "year_built": 1978, "beds": 3, "baths": 2.0, "condition": "fair", "condition_score": 0.45, "list_price": 85000, "arv": 115000, "rent": 1050, "section_8_rent": 1150, "type": "sfr"},
    {"address": "567 Maple Ave", "city": "Cleveland", "state": "OH", "zip": "44105", "sqft": 1200, "year_built": 1965, "beds": 3, "baths": 1.0, "condition": "fair", "condition_score": 0.40, "list_price": 62000, "arv": 90000, "rent": 850, "section_8_rent": 950, "type": "sfr"},
    {"address": "890 Pine Rd", "city": "Detroit", "state": "MI", "zip": "48227", "sqft": 1350, "year_built": 1955, "beds": 3, "baths": 1.5, "condition": "poor", "condition_score": 0.30, "list_price": 45000, "arv": 75000, "rent": 800, "section_8_rent": 900, "type": "sfr"},
    {"address": "234 Elm St", "city": "Birmingham", "state": "AL", "zip": "35208", "sqft": 1600, "year_built": 1972, "beds": 4, "baths": 2.0, "condition": "fair", "condition_score": 0.50, "list_price": 78000, "arv": 110000, "rent": 1100, "section_8_rent": 1200, "type": "sfr"},
    {"address": "456 Cedar Blvd", "city": "Indianapolis", "state": "IN", "zip": "46218", "sqft": 1800, "year_built": 1968, "beds": 4, "baths": 2.0, "condition": "fair", "condition_score": 0.48, "list_price": 95000, "arv": 135000, "rent": 1250, "section_8_rent": 1350, "type": "sfr"},
    # Duplex deals
    {"address": "789 Birch Ln", "city": "Kansas City", "state": "MO", "zip": "64130", "sqft": 2400, "year_built": 1962, "beds": 4, "baths": 2.0, "condition": "fair", "condition_score": 0.45, "list_price": 110000, "arv": 160000, "rent": 1900, "section_8_rent": 2100, "type": "duplex"},
    {"address": "321 Walnut Dr", "city": "Columbus", "state": "OH", "zip": "43205", "sqft": 2100, "year_built": 1970, "beds": 4, "baths": 2.0, "condition": "good", "condition_score": 0.65, "list_price": 125000, "arv": 175000, "rent": 2000, "section_8_rent": 2200, "type": "duplex"},
    # Good condition / tighter DSCR
    {"address": "654 Spruce Way", "city": "St. Louis", "state": "MO", "zip": "63118", "sqft": 1550, "year_built": 1985, "beds": 3, "baths": 2.0, "condition": "good", "condition_score": 0.70, "list_price": 115000, "arv": 145000, "rent": 1150, "section_8_rent": 1200, "type": "sfr"},
    {"address": "987 Ash Ct", "city": "Louisville", "state": "KY", "zip": "40214", "sqft": 1400, "year_built": 1990, "beds": 3, "baths": 2.0, "condition": "good", "condition_score": 0.72, "list_price": 105000, "arv": 130000, "rent": 1050, "section_8_rent": 1100, "type": "sfr"},
    # High rehab / distressed
    {"address": "147 Hickory Pl", "city": "Baltimore", "state": "MD", "zip": "21215", "sqft": 1700, "year_built": 1940, "beds": 4, "baths": 2.0, "condition": "distressed", "condition_score": 0.15, "list_price": 38000, "arv": 115000, "rent": 1100, "section_8_rent": 1250, "type": "sfr"},
    {"address": "258 Willow St", "city": "Philadelphia", "state": "PA", "zip": "19132", "sqft": 1300, "year_built": 1935, "beds": 3, "baths": 1.0, "condition": "distressed", "condition_score": 0.20, "list_price": 35000, "arv": 95000, "rent": 950, "section_8_rent": 1100, "type": "sfr"},
    # Triplex
    {"address": "369 Magnolia Ave", "city": "Dayton", "state": "OH", "zip": "45417", "sqft": 3200, "year_built": 1958, "beds": 6, "baths": 3.0, "condition": "fair", "condition_score": 0.42, "list_price": 135000, "arv": 195000, "rent": 2700, "section_8_rent": 3000, "type": "triplex"},
    # Borderline / marginal
    {"address": "741 Poplar Rd", "city": "Jackson", "state": "MS", "zip": "39209", "sqft": 1250, "year_built": 1975, "beds": 3, "baths": 1.5, "condition": "fair", "condition_score": 0.44, "list_price": 55000, "arv": 72000, "rent": 750, "section_8_rent": 850, "type": "sfr"},
    {"address": "852 Sycamore Blvd", "city": "Akron", "state": "OH", "zip": "44306", "sqft": 1100, "year_built": 1960, "beds": 2, "baths": 1.0, "condition": "fair", "condition_score": 0.40, "list_price": 48000, "arv": 65000, "rent": 650, "section_8_rent": 720, "type": "sfr"},
    # Strong performers
    {"address": "963 Cypress Dr", "city": "Memphis", "state": "TN", "zip": "38116", "sqft": 1650, "year_built": 1982, "beds": 3, "baths": 2.0, "condition": "fair", "condition_score": 0.52, "list_price": 88000, "arv": 120000, "rent": 1200, "section_8_rent": 1300, "type": "sfr"},
    {"address": "174 Locust Ln", "city": "Cincinnati", "state": "OH", "zip": "45206", "sqft": 1900, "year_built": 1974, "beds": 4, "baths": 2.5, "condition": "good", "condition_score": 0.65, "list_price": 132000, "arv": 170000, "rent": 1500, "section_8_rent": 1600, "type": "sfr"},
    {"address": "285 Chestnut Ave", "city": "Pittsburgh", "state": "PA", "zip": "15210", "sqft": 1750, "year_built": 1968, "beds": 4, "baths": 2.0, "condition": "fair", "condition_score": 0.50, "list_price": 98000, "arv": 140000, "rent": 1300, "section_8_rent": 1400, "type": "sfr"},
    # Fourplex
    {"address": "396 Pecan St", "city": "Oklahoma City", "state": "OK", "zip": "73109", "sqft": 4400, "year_built": 1965, "beds": 8, "baths": 4.0, "condition": "fair", "condition_score": 0.45, "list_price": 185000, "arv": 260000, "rent": 3600, "section_8_rent": 4000, "type": "fourplex"},
    # Overpriced / likely reject
    {"address": "507 Rosewood Ct", "city": "Austin", "state": "TX", "zip": "78745", "sqft": 1400, "year_built": 2005, "beds": 3, "baths": 2.0, "condition": "excellent", "condition_score": 0.90, "list_price": 385000, "arv": 420000, "rent": 2200, "section_8_rent": 2100, "type": "sfr"},
    # Cash flow machine
    {"address": "618 Dogwood Dr", "city": "Toledo", "state": "OH", "zip": "43609", "sqft": 1500, "year_built": 1971, "beds": 3, "baths": 2.0, "condition": "fair", "condition_score": 0.48, "list_price": 52000, "arv": 78000, "rent": 875, "section_8_rent": 975, "type": "sfr"},
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
