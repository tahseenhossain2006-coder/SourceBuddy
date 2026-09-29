# sourceai/interfaces/factory.py
"""
Factory for intelligent components.

Returns deterministic or LLM-backed implementations based on the
AI_ENABLED setting. The rest of the system calls these getters and
remains agnostic about which implementation is active.

When AI_ENABLED=false (default), every getter returns a deterministic
implementation. When true, the factory would return LLM-backed
implementations — those are not implemented in this V1 but the hook
points exist.
"""
from __future__ import annotations

import logging

from sourceai.config.settings import settings
from sourceai.interfaces.base import (
    RequirementInterpreter,
    QueryExpander,
    ResearchReasoner,
    SemanticExtractor,
    ProductExtractor,
    SupplierClassifier,
    EvidenceInterpreter,
    SemanticRanker,
    RecommendationEngine,
    AnswerGenerator,
)

logger = logging.getLogger(__name__)


def _ai_enabled() -> bool:
    return bool(getattr(settings, "AI_ENABLED", False))


# ---------------------------------------------------------------------------
# Getters — deterministic when AI_ENABLED=false
# ---------------------------------------------------------------------------

def get_requirement_interpreter() -> RequirementInterpreter:
    if _ai_enabled():
        # Future: LLMRequirementInterpreter()
        logger.warning(
            "AI_ENABLED=true but LLMRequirementInterpreter not implemented; "
            "falling back to deterministic"
        )
    from sourceai.interfaces.deterministic import DeterministicRequirementInterpreter
    return DeterministicRequirementInterpreter()


def get_query_expander() -> QueryExpander:
    from sourceai.interfaces.deterministic import DeterministicQueryExpander
    return DeterministicQueryExpander()


def get_research_reasoner() -> ResearchReasoner:
    from sourceai.interfaces.deterministic import DeterministicResearchReasoner
    return DeterministicResearchReasoner()


def get_semantic_extractor() -> SemanticExtractor:
    if _ai_enabled():
        logger.warning(
            "AI_ENABLED=true but LLMSemanticExtractor not implemented; "
            "falling back to deterministic"
        )
    from sourceai.interfaces.deterministic import DeterministicSemanticExtractor
    return DeterministicSemanticExtractor()


def get_product_extractor() -> ProductExtractor:
    from sourceai.interfaces.deterministic import DeterministicProductExtractor
    return DeterministicProductExtractor()


def get_supplier_classifier() -> SupplierClassifier:
    from sourceai.interfaces.deterministic import DeterministicSupplierClassifier
    return DeterministicSupplierClassifier()


def get_evidence_interpreter() -> EvidenceInterpreter:
    from sourceai.interfaces.deterministic import DeterministicEvidenceInterpreter
    return DeterministicEvidenceInterpreter()


def get_semantic_ranker() -> SemanticRanker:
    from sourceai.interfaces.deterministic import DeterministicSemanticRanker
    return DeterministicSemanticRanker()


def get_recommendation_engine() -> RecommendationEngine:
    from sourceai.interfaces.deterministic import DeterministicRecommendationEngine
    return DeterministicRecommendationEngine()


def get_answer_generator() -> AnswerGenerator:
    from sourceai.interfaces.deterministic import DeterministicAnswerGenerator
    return DeterministicAnswerGenerator()