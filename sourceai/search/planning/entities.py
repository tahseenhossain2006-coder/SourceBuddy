# sourceai/search/planning/entities.py
import re
from typing import Dict


class EntityExtractor:
    """Extract product, quantity, supplier type, location, country from a query."""

    # Common supplier type keywords (order matters: more specific first).
    SUPPLIER_TYPES = {
        "manufacturer": ["manufacturer", "factory", "maker", "producer"],
        "distributor": ["distributor"],
        "wholesaler": ["wholesaler", "wholesale"],
        "exporter": ["exporter", "export house"],
        "trader": ["trader", "trading company"],
        "retailer": ["retailer", "retail"],
        "supplier": ["supplier", "vendor", "provider"],
    }

    COUNTRY_PATTERN = re.compile(
        r'\b(india|china|usa|uk|germany|japan|korea|vietnam|bangladesh|'
        r'pakistan|indonesia|thailand|turkey|brazil|mexico)\b',
        re.I,
    )

    LOCATION_PATTERN = re.compile(
        r'\b(in|near|at|from|located\s+in)\s+([\w\s]+?)(?=\s+with|\s+for|\s+and|\s*$)',
        re.I,
    )

    # Quantity: "1000 pcs", "5K pieces", "10 cartons", "need 5000 units"
    QUANTITY_PATTERN = re.compile(
        r'\b(\d+(?:\.\d+)?)\s*([kKmM])?\s*'
        r'(pieces?|pcs?|units?|cartons?|boxes?|cases?|kgs?|grams?|'
        r'liters?|litres?|sets?|dozens?)\b',
        re.I,
    )

    @classmethod
    def extract(cls, query: str) -> Dict[str, object]:
        result: Dict[str, object] = {
            "product": None,
            "quantity": None,
            "quantity_unit": None,
            "supplier_type": None,
            "location": None,
            "country": None,
        }

        # ---- Country ----
        cnt_match = cls.COUNTRY_PATTERN.search(query)
        if cnt_match:
            result["country"] = cnt_match.group(0).lower().capitalize()

        # ---- Location (city-level) ----
        loc_match = cls.LOCATION_PATTERN.search(query)
        if loc_match:
            loc_str = loc_match.group(2).strip()
            loc_str = re.sub(
                r'\s+(with|for|and|of|in|to|from)$', '',
                loc_str, flags=re.I,
            )
            # Don't store a country name as a city
            if loc_str and (result["country"] is None or
                            loc_str.lower() != str(result["country"]).lower()):
                result["location"] = loc_str

        # ---- Quantity ----
        qty_match = cls.QUANTITY_PATTERN.search(query)
        if qty_match:
            raw = qty_match.group(1)
            suffix = (qty_match.group(2) or "").lower()
            try:
                qty = float(raw)
            except ValueError:
                qty = None
            if qty is not None:
                if suffix == "k":
                    qty *= 1_000
                elif suffix == "m":
                    qty *= 1_000_000
                result["quantity"] = int(qty)
                result["quantity_unit"] = qty_match.group(3).lower()

        # ---- Supplier type ----
        lower = query.lower()
        for s_type, keywords in cls.SUPPLIER_TYPES.items():
            if any(kw in lower for kw in keywords):
                result["supplier_type"] = s_type
                break

        # ---- Product (delegated to SearchPlanner._guess_product) ----
        # Left as None here; SearchPlanner fills it in.

        return result