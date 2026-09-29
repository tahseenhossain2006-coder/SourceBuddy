# sourceai/search/planning/query_expansion.py
from typing import List, Set
from ..models.search_plan import SearchPlan

class QueryExpander:
    """Generate multiple search query variations from a structured SearchPlan."""

    @staticmethod
    def expand(plan) -> List[str]:
        """Return a list of query variations."""
        base = plan.product or ""
        supplier_type = plan.supplier_type or "supplier"
        location = plan.location or ""
        variations = set()

        # 1. Base: product + supplier type + location
        if base and supplier_type:
            q = f"{base} {supplier_type}"
            if location:
                q += f" {location}"
            variations.add(q)

        # 2. Product + location + supplier type (different order)
        if base and location:
            q = f"{base} {location} {supplier_type}"
            variations.add(q)

        # 3. Product + supplier type only (if no location)
        if base and supplier_type:
            variations.add(f"{base} {supplier_type}")

        # 4. Use synonyms: manufacturer, factory, maker, etc.
        synonyms = {
            "manufacturer": ["manufacturer", "factory", "maker", "producer"],
            "supplier": ["supplier", "vendor", "provider", "source"],
            "distributor": ["distributor", "distributor company"],
            "wholesaler": ["wholesaler", "wholesale"],
        }

        for key, syns in synonyms.items():
            if supplier_type and key in supplier_type or supplier_type in syns:
                for syn in syns:
                    if syn != supplier_type:
                        q = f"{base} {syn}"
                        if location:
                            q += f" {location}"
                        variations.add(q)

        # 5. Add common variations with "custom", "OEM", "bulk", etc.
        for modifier in ["custom", "OEM", "bulk", "private label"]:
            if base:
                q = f"{modifier} {base} {supplier_type}"
                if location:
                    q += f" {location}"
                variations.add(q)

        # 6. Add "in" location format
        if location and base:
            variations.add(f"{base} in {location}")

        # 7. Remove duplicates and sort
        return sorted(list(variations))