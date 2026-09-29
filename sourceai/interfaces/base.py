# sourceai/interfaces/base.py
"""
Abstract interfaces for SourceAI's intelligent components.

Every component that may eventually benefit from an LLM is defined here
as an abstract base class. The rest of the system depends on these
interfaces, not on concrete implementations. Swapping a deterministic
implementation for an LLM implementation is done by the factory in
`sourceai.interfaces.factory`, driven by the AI_ENABLED setting.

No LLM code lives in this module.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sourceai.llm.structured import (
    RequirementResult,
    SupplierExtractionResult,
    ProductExtractionResult,
    ComparisonResult,
    RiskAnalysisResult,
)


# ---------------------------------------------------------------------------
# Query understanding
# ---------------------------------------------------------------------------

class RequirementInterpreter(ABC):
    """
    Convert a natural-language user query into structured requirements.
    """

    @abstractmethod
    def interpret(self, user_query: str) -> RequirementResult:
        ...


class QueryExpander(ABC):
    """
    Given a search plan, produce query variants to widen recall.
    """

    @abstractmethod
    def expand(self, plan: Any) -> List[str]:
        ...


class ResearchReasoner(ABC):
    """
    Given the current state of a research loop (plan + found suppliers),
    decide whether to refine the plan and what to try next.
    """

    @abstractmethod
    def refine(
        self,
        plan: Any,
        suppliers: List[Dict[str, Any]],
    ) -> Any:
        ...


# ---------------------------------------------------------------------------
# Extraction and classification
# ---------------------------------------------------------------------------

class SemanticExtractor(ABC):
    """
    Extract structured supplier data from one crawled page.
    """

    @abstractmethod
    def extract(
        self, page: Dict[str, Any]
    ) -> SupplierExtractionResult:
        ...

    def extract_batch(
        self, pages: List[Dict[str, Any]]
    ) -> List[SupplierExtractionResult]:
        """Default batch implementation — override only if needed."""
        out: List[SupplierExtractionResult] = []
        for p in pages:
            try:
                out.append(self.extract(p))
            except Exception:
                continue
        return out


class ProductExtractor(ABC):
    """
    Extract structured product data from one crawled page.
    """

    @abstractmethod
    def extract(
        self, page: Dict[str, Any]
    ) -> ProductExtractionResult:
        ...


class SupplierClassifier(ABC):
    """
    Classify a supplier record: manufacturer, distributor, wholesaler, etc.
    Returns (label, signals) where signals are evidence strings.
    """

    @abstractmethod
    def classify(self, text: str) -> tuple[Optional[str], List[str]]:
        ...


class EvidenceInterpreter(ABC):
    """
    Attach per-field evidence to a supplier extraction result.
    """

    @abstractmethod
    def attach_evidence(
        self,
        text: str,
        url: str,
        fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...


# ---------------------------------------------------------------------------
# Ranking, comparison, explanation
# ---------------------------------------------------------------------------

class SemanticRanker(ABC):
    """
    Score and order suppliers against search constraints.
    """

    @abstractmethod
    def rank(
        self,
        suppliers: List[Any],
        constraints: Dict[str, Any],
    ) -> List[Any]:
        ...


class RecommendationEngine(ABC):
    """
    Produce a factual summary of the suppliers found.
    """

    @abstractmethod
    def summarize(
        self,
        suppliers: List[Any],
        plan: Any,
    ) -> str:
        ...


class AnswerGenerator(ABC):
    """
    Generate the final user-facing answer text.
    """

    @abstractmethod
    def generate(
        self,
        suppliers: List[Any],
        plan: Any,
    ) -> str:
        ...