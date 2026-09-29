import re
from typing import Optional
from ..models.search_plan import Intent

class IntentDetector:

    _patterns = {
        Intent.SUPPLIER_SEARCH: re.compile(r'\b(supplier|suppliers|vendor|vendors)\b', re.I),
        Intent.MANUFACTURER_SEARCH: re.compile(r'\b(manufacturer|manufacturers|factory|factories|maker|makers)\b', re.I),
        Intent.DISTRIBUTOR_SEARCH: re.compile(r'\b(distributor|distributors|distributor\s+company)\b', re.I),
        Intent.WHOLESALER_SEARCH: re.compile(r'\b(wholesaler|wholesalers|wholesale)\b', re.I),
        Intent.PRICE_SEARCH: re.compile(r'\b(price|pricing|cost|cheap|expensive|budget)\b', re.I),
        Intent.COMPARISON_SEARCH: re.compile(r'\b(compare|comparison|vs|versus|against)\b', re.I),
        Intent.PRODUCT_SEARCH: re.compile(r'\b(product|products|item|items|goods)\b', re.I),
    }

    # Common stopwords to ignore for product fallback
    _stopwords = {"find", "search", "need", "want", "looking", "for", "in", "with", "under", "below", "less", "than", "at", "most", "price", "moq", "minimum", "order", "quantity"}

    @classmethod
    def detect(cls, query: str) -> Intent:
        # First try explicit patterns
        for intent, pattern in cls._patterns.items():
            if pattern.search(query):
                return intent

        # Fallback: if query has non‑stopword words, treat as PRODUCT_SEARCH
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query)
        meaningful = [w for w in words if w.lower() not in cls._stopwords]
        if meaningful:
            return Intent.PRODUCT_SEARCH

        return Intent.GENERAL_WEB_SEARCH