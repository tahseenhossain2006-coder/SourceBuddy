# sourceai/interfaces/deterministic.py
"""
Deterministic implementations of the interface layer.

Each implementation delegates to existing deterministic code — this
module is a thin adapter, not a reimplementation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sourceai.interfaces.base import (
    RequirementInterpreter,
    QueryExpander as QueryExpanderIface,
    ResearchReasoner,
    SemanticExtractor,
    ProductExtractor,
    SupplierClassifier,
    EvidenceInterpreter,
    SemanticRanker,
    RecommendationEngine,
    AnswerGenerator,
)
from sourceai.llm.structured import (
    RequirementResult,
    SupplierExtractionResult,
    ProductExtractionResult,
)


# ---------------------------------------------------------------------------
# Requirement interpretation (deterministic)
# ---------------------------------------------------------------------------

class DeterministicRequirementInterpreter(RequirementInterpreter):
    """
    Rule-based interpretation of a user query.

    Delegates to the existing planner — no LLM, no network.
    """

    def interpret(self, user_query: str) -> RequirementResult:
        from sourceai.search.planner import SearchPlanner

        plan = SearchPlanner().plan(user_query or "")
        entities = plan.entities or {}
        constraints = plan.constraints or {}

        return RequirementResult(
            product=entities.get("product"),
            quantity=entities.get("quantity"),
            currency=entities.get("currency"),
            target_country=entities.get("country"),
            target_city=entities.get("city"),
            moq=constraints.get("max_moq"),
            supplier_type=entities.get("supplier_type"),
            certifications=entities.get("certifications") or [],
        )


# ---------------------------------------------------------------------------
# Query expansion (deterministic)
# ---------------------------------------------------------------------------

class DeterministicQueryExpander(QueryExpanderIface):
    """
    Rule-based query expansion using the existing planning module.
    """

    def expand(self, plan: Any) -> List[str]:
        from sourceai.search.planning.query_expansion import QueryExpander as _Expander

        try:
            return _Expander.expand(plan) or []
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Research reasoning (deterministic — no refinement)
# ---------------------------------------------------------------------------

class DeterministicResearchReasoner(ResearchReasoner):
    """
    No-op refinement.

    The deterministic path does not try to reason about the next query.
    Returning the plan unchanged terminates the research loop cleanly.
    """

    def refine(self, plan: Any, suppliers: List[Dict[str, Any]]) -> Any:
        return plan


# ---------------------------------------------------------------------------
# Supplier extraction (deterministic)
# ---------------------------------------------------------------------------

class DeterministicSemanticExtractor(SemanticExtractor):
    """
    Wraps DeterministicSupplierExtractor, which uses regex + dictionaries.
    """

    def __init__(self) -> None:
        from sourceai.llm.deterministic import DeterministicSupplierExtractor

        self._impl = DeterministicSupplierExtractor()

    def extract(self, page: Dict[str, Any]) -> SupplierExtractionResult:
        return self._impl.extract(page)


class DeterministicProductExtractor(ProductExtractor):
    """
    Minimal deterministic product extraction.

    Products are already captured by DeterministicSupplierExtractor's
    `products` field. This class projects them into the ProductExtractionResult
    shape, one entry per page.
    """

    def extract(self, page: Dict[str, Any]) -> ProductExtractionResult:
        from sourceai.llm.deterministic import DeterministicSupplierExtractor

        supplier = DeterministicSupplierExtractor().extract(page)
        return ProductExtractionResult(
            product_name=(supplier.products or [None])[0],
            variants=list(supplier.products or []),
            price=supplier.price,
            currency=supplier.currency,
            moq=supplier.moq,
            supplier=supplier.supplier_name,
            source_url=(supplier.source_urls or [None])[0],
            confidence=supplier.confidence,
        )


class DeterministicSupplierClassifier(SupplierClassifier):
    """
    Wraps the dictionary-based classifier from the deterministic extractor.
    """

    def classify(self, text: str) -> tuple[Optional[str], List[str]]:
        from sourceai.llm.deterministic import _detect_supplier_type

        return _detect_supplier_type(text)


class DeterministicEvidenceInterpreter(EvidenceInterpreter):
    """
    Wraps the evidence builder from the deterministic extractor.
    """

    def attach_evidence(
        self,
        text: str,
        url: str,
        fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        from sourceai.llm.deterministic import _build_evidence

        return _build_evidence(text, url, fields)


# ---------------------------------------------------------------------------
# Ranking, summary, final answer
# ---------------------------------------------------------------------------

class DeterministicSemanticRanker(SemanticRanker):
    """
    Wraps the deterministic ranker in LLMIntegration.
    """

    def __init__(self) -> None:
        from sourceai.llm.integration import LLMIntegration

        # Pass a router that will never be used (deterministic path)
        self._impl = LLMIntegration(router=None)  # type: ignore[arg-type]

    def rank(self, suppliers: List[Any], constraints: Dict[str, Any]) -> List[Any]:
        return self._impl.rank_suppliers(suppliers, constraints)


class DeterministicRecommendationEngine(RecommendationEngine):
    """
    Factual summary derived from the supplier list. No recommendations.
    """

    def summarize(self, suppliers: List[Any], plan: Any) -> str:
        if not suppliers:
            return "No suppliers found matching your criteria."
        return f"{len(suppliers)} supplier(s) matched the search."


class DeterministicAnswerGenerator(AnswerGenerator):
    """
    Wraps the existing deterministic answer builder.
    """

    def __init__(self) -> None:
        from sourceai.llm.integration import LLMIntegration

        self._impl = LLMIntegration(router=None)  # type: ignore[arg-type]

    def generate(self, suppliers: List[Any], plan: Any) -> str:
        return self._impl.generate_final_answer(suppliers, plan)