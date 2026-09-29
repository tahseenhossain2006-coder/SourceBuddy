# sourceai/search/planning/query_normalizer.py
import re

class QueryNormalizer:
    """Remove only conversational filler words. Keep product, supplier type, location, constraints."""

    _filler_patterns = [
        re.compile(r'\b(please|can you|could you|would you|i need|i want|looking for|find me|get me|show me|help me|search for|tell me|give me)\b', re.I),
    ]

    @classmethod
    def normalize(cls, query: str) -> str:
        normalized = query.strip()
        for pat in cls._filler_patterns:
            normalized = pat.sub('', normalized)
        # Collapse spaces and trim
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized