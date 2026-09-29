# sourceai/search/models/search_plan.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class Intent(str, Enum):
    SUPPLIER_SEARCH = "supplier_search"
    PRODUCT_SEARCH = "product_search"
    MANUFACTURER_SEARCH = "manufacturer_search"
    DISTRIBUTOR_SEARCH = "distributor_search"
    WHOLESALER_SEARCH = "wholesaler_search"
    PRICE_SEARCH = "price_search"
    COMPARISON_SEARCH = "comparison_search"
    GENERAL_WEB_SEARCH = "general_web_search"

@dataclass
class SearchPlan:
    """
    A strongly-typed representation of a structured search plan.
    """
    original_query: str
    normalized_query: str
    intent: Intent
    product: Optional[str] = None
    supplier_type: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    query_variations: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    priority: str = "medium"   # "high", "medium", "low"
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "intent": self.intent.value,
            "product": self.product,
            "supplier_type": self.supplier_type,
            "location": self.location,
            "country": self.country,
            "keywords": self.keywords,
            "constraints": self.constraints,
            "query_variations": self.query_variations,
            "required_fields": self.required_fields,
            "priority": self.priority,
            "confidence": self.confidence,
        }