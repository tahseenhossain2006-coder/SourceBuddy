# sourceai/search/planner.py
"""
Search planner.

Wires the deterministic parsing modules in `sourceai.search.planning`
into a runtime `SearchPlan` object consumed by `SearchAgent`.
"""
import logging
import re
from typing import Any, Dict, List

from dataclasses import dataclass, field

from sourceai.search.planning.constraints import ConstraintExtractor
from sourceai.search.planning.entities import EntityExtractor
from sourceai.search.planning.intent import IntentDetector
from sourceai.search.planning.query_expansion import QueryExpander
from sourceai.search.planning.query_normalizer import QueryNormalizer
from sourceai.search.models.search_plan import SearchPlan as RichSearchPlan

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Runtime SearchPlan — the shape SearchAgent expects
# ---------------------------------------------------------------------------

@dataclass
class SearchPlan:
    original_query: str
    normalized_query: str
    intent: str
    entities: Dict[str, Any]
    constraints: Dict[str, Any]
    keywords: List[str]
    expanded_queries: List[str]
    preferred_engines: List[str] = field(default_factory=list)
    max_results: int = 20
    max_pages: int = 10
    crawl_enabled: bool = True
    extraction_enabled: bool = True
    verification_required: bool = True
    research_depth: int = 1

    def model_dump(self) -> Dict[str, Any]:
        return {
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "intent": self.intent,
            "entities": self.entities,
            "constraints": self.constraints,
            "keywords": self.keywords,
            "expanded_queries": self.expanded_queries,
            "preferred_engines": self.preferred_engines,
            "max_results": self.max_results,
            "max_pages": self.max_pages,
            "crawl_enabled": self.crawl_enabled,
            "extraction_enabled": self.extraction_enabled,
            "verification_required": self.verification_required,
            "research_depth": self.research_depth,
        }


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------

class SearchPlanner:
    """
    Deterministic query planner.

    Calls the parsing modules in `sourceai.search.planning` to extract
    intent, entities, and constraints from a natural-language query, and
    produces the runtime SearchPlan object consumed by SearchAgent.
    """

    _MAX_VARIANTS = 8

    def plan(self, query: str) -> SearchPlan:
        original = query or ""
        normalized = QueryNormalizer.normalize(original)

        # 1. Intent
        try:
            intent = IntentDetector.detect(normalized)
            intent_str = intent.value if hasattr(intent, "value") else str(intent)
        except Exception as exc:
            logger.warning("Intent detection failed: %s", exc)
            intent_str = "supplier_search"

        # 2. Entities
        try:
            entities_raw = EntityExtractor.extract(normalized)
        except Exception as exc:
            logger.warning("Entity extraction failed: %s", exc)
            entities_raw = {}

        # 3. Constraints
        try:
            constraints = ConstraintExtractor.extract(normalized)
        except Exception as exc:
            logger.warning("Constraint extraction failed: %s", exc)
            constraints = {}

        # 4. Product fallback — EntityExtractor leaves this to the caller.
        product = entities_raw.get("product") or self._guess_product(normalized)
        if product:
            entities_raw["product"] = product

        # 5. Currency promotes from constraints to entities for API clarity.
        if constraints.get("currency") and not entities_raw.get("currency"):
            entities_raw["currency"] = constraints["currency"]

        # 6. Build a rich plan to feed the expander.
        try:
            rich = RichSearchPlan(
                original_query=original,
                normalized_query=normalized,
                intent=intent,
                product=product,
                supplier_type=entities_raw.get("supplier_type"),
                location=entities_raw.get("location"),
                country=entities_raw.get("country"),
                constraints=constraints,
            )
            variants = QueryExpander.expand(rich)
        except Exception as exc:
            logger.warning("Query expansion failed: %s", exc)
            variants = [normalized]

        # Ensure the original query is always first.
        seen = set()
        expanded: List[str] = []
        for q in [original] + variants:
            q = q.strip()
            if q and q not in seen:
                seen.add(q)
                expanded.append(q)
            if len(expanded) >= self._MAX_VARIANTS:
                break

        # 7. Keywords: lowercase, deduped, stopword-stripped.
        keywords = self._keywords(normalized)

        return SearchPlan(
            original_query=original,
            normalized_query=normalized,
            intent=intent_str,
            entities=entities_raw,
            constraints=constraints,
            keywords=keywords,
            expanded_queries=expanded,
        )

    # ------------------------------------------------------------------ helpers
    _STOPWORDS = {
        "a", "an", "the", "and", "or", "of", "for", "in", "on", "at", "to",
        "with", "by", "from", "under", "below", "above", "over", "less",
        "than", "at", "most", "need", "want", "looking", "find", "search",
        "please", "me", "my", "our", "is", "are", "be", "as",
    }

    _PRODUCT_TRAILING = {
        "supplier", "suppliers", "manufacturer", "manufacturers", "factory",
        "factories", "wholesaler", "wholesalers", "distributor",
        "distributors", "exporter", "exporters", "trader", "traders",
        "vendor", "vendors", "oem", "odm",
    }

    _PRODUCT_LEADING = {
        "find", "search", "get", "show", "need", "want", "looking", "for",
        "buy", "purchase", "source", "custom", "bulk",
    }

    _UNIT_TOKENS = {
        "pcs", "pc", "pieces", "piece", "units", "unit",
        "cartons", "carton", "boxes", "box", "cases", "case",
        "kgs", "kg", "grams", "gram", "g",
        "liters", "liter", "litres", "litre",
        "sets", "set", "dozens", "dozen",
    }

    @classmethod
    def _keywords(cls, query: str) -> List[str]:
        words = [w.lower() for w in query.split()]
        seen = set()
        out: List[str] = []
        for w in words:
            if w in cls._STOPWORDS:
                continue
            if w not in seen:
                seen.add(w)
                out.append(w)
        return out

    @classmethod
    def _guess_product(cls, query: str) -> str:
        """
        Deterministic product heuristic.

        Take the words between any leading filler verb and any trailing
        supplier-type keyword, drop quantity prefixes, drop stopwords, and
        return what's left. Deliberately simple and honest — if nothing
        sensible is left, return "".
        """
        tokens = query.strip().split()
        if not tokens:
            return ""

        # Trim leading filler verbs
        while tokens and tokens[0].lower() in cls._PRODUCT_LEADING:
            tokens.pop(0)

        # Trim trailing supplier-type keywords
        while tokens and tokens[-1].lower() in cls._PRODUCT_TRAILING:
            tokens.pop()

        # Trim leading quantity like "1000", "1000k", "5K", "10.5"
        while tokens and re.match(r'^\d+(?:\.\d+)?(?:[kKmM])?$', tokens[0]):
            tokens.pop(0)

        # Trim a trailing unit token after a quantity ("pcs", "pieces", ...)
        if tokens and tokens[0].lower() in cls._UNIT_TOKENS:
            tokens.pop(0)

        # Trim trailing "in <location>" / "from <location>"
        for prep in ("in", "from", "at", "near"):
            lowered = [t.lower() for t in tokens]
            if prep in lowered:
                idx = lowered.index(prep)
                if idx > 0:
                    tokens = tokens[:idx]
                    break

        # Remove everything from the first constraint marker onward
        stop_markers = {
            "moq", "minimum", "min", "under", "below", "less",
            "price", "budget", "max", "maximum", "quantity", "cost", "rate",
        }
        for i, t in enumerate(tokens):
            if t.lower() in stop_markers:
                tokens = tokens[:i]
                break

        # Drop remaining stopwords
        product_tokens = [
            t for t in tokens
            if t.lower() not in cls._STOPWORDS and t.strip()
        ]

        return " ".join(product_tokens).strip()