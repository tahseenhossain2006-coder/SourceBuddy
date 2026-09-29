"""Interface factory tests."""
import pytest

from sourceai.interfaces import factory
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


# ---------------------------------------------------------------------------
# Factory returns the correct interface type
# ---------------------------------------------------------------------------

def test_requirement_interpreter_type():
    impl = factory.get_requirement_interpreter()
    assert isinstance(impl, RequirementInterpreter)


def test_query_expander_type():
    assert isinstance(factory.get_query_expander(), QueryExpander)


def test_research_reasoner_type():
    assert isinstance(factory.get_research_reasoner(), ResearchReasoner)


def test_semantic_extractor_type():
    assert isinstance(factory.get_semantic_extractor(), SemanticExtractor)


def test_product_extractor_type():
    assert isinstance(factory.get_product_extractor(), ProductExtractor)


def test_supplier_classifier_type():
    assert isinstance(factory.get_supplier_classifier(), SupplierClassifier)


def test_evidence_interpreter_type():
    assert isinstance(factory.get_evidence_interpreter(), EvidenceInterpreter)


def test_semantic_ranker_type():
    assert isinstance(factory.get_semantic_ranker(), SemanticRanker)


def test_recommendation_engine_type():
    assert isinstance(factory.get_recommendation_engine(), RecommendationEngine)


def test_answer_generator_type():
    assert isinstance(factory.get_answer_generator(), AnswerGenerator)


# ---------------------------------------------------------------------------
# Behavioural smoke tests — deterministic path
# ---------------------------------------------------------------------------

def test_requirement_interpreter_extracts_moq():
    impl = factory.get_requirement_interpreter()
    req = impl.interpret("stainless steel bottle supplier India MOQ 500")
    assert req.moq == 500


def test_research_reasoner_returns_plan_unchanged():
    impl = factory.get_research_reasoner()
    sentinel = object()
    assert impl.refine(sentinel, []) is sentinel


def test_supplier_classifier_detects_manufacturer():
    impl = factory.get_supplier_classifier()
    label, signals = impl.classify("We are a manufacturer of steel bottles")
    assert label == "manufacturer"
    assert signals


def test_semantic_extractor_returns_result():
    impl = factory.get_semantic_extractor()
    page = {
        "url": "https://acme.example/",
        "title": "Acme Metals Pvt Ltd",
        "text": "Acme Metals Pvt Ltd manufactures steel bottles in India. MOQ 100.",
    }
    result = impl.extract(page)
    assert result.supplier_name is not None


def test_semantic_extractor_batch_tolerates_bad_pages():
    impl = factory.get_semantic_extractor()
    pages = [
        {"url": "https://a/", "title": "A Co Pvt Ltd", "text": "manufacturer MOQ 100"},
        {},  # empty — should not raise
        {"url": "https://b/", "title": "", "text": ""},
    ]
    out = impl.extract_batch(pages)
    assert len(out) >= 1


def test_evidence_interpreter_returns_dict():
    impl = factory.get_evidence_interpreter()
    ev = impl.attach_evidence(
        "Acme Metals Pvt Ltd is in India",
        "https://acme.example/",
        {"supplier_name": "Acme Metals Pvt Ltd", "country": "India"},
    )
    assert isinstance(ev, dict)
    assert "supplier_name" in ev


def test_recommendation_engine_empty_message():
    impl = factory.get_recommendation_engine()
    assert "No suppliers" in impl.summarize([], None)


def test_recommendation_engine_counts_suppliers():
    impl = factory.get_recommendation_engine()
    msg = impl.summarize([{}, {}, {}], None)
    assert "3" in msg


def test_answer_generator_empty_message():
    impl = factory.get_answer_generator()
    assert "No suppliers" in impl.generate([], None)


# ---------------------------------------------------------------------------
# AI flag doesn't crash the factory
# ---------------------------------------------------------------------------

def test_ai_enabled_true_still_returns_something(monkeypatch):
    from sourceai.config import settings as s
    monkeypatch.setattr(s.settings, "AI_ENABLED", True)
    # Factory logs a warning but returns deterministic impls
    assert factory.get_requirement_interpreter() is not None
    assert factory.get_semantic_extractor() is not None