"""Deterministic extraction tests (no LLM, no DB, no network)."""
import pytest

from sourceai.llm.deterministic import (
    DeterministicSupplierExtractor,
    _is_product_candidate,
    _extract_products,
    _compute_confidence,
    _compute_completeness,
)
from sourceai.supplier.normalizer import (
    identity_key,
    merge_records,
    normalize_suppliers,
)
from sourceai.supplier.contradictions import (
    detect_contradictions,
    detect_all,
)


# ---------------------------------------------------------------------------
# Product extraction — noise rejection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("line", [
    "MASTER CARTOON",
    "280 PCS IN SINGLE CARTOON",
    "82% Response Rate★★★★★★★★★★4.4(196)",
    "★★★★★ 4.8 (234)",
    "Share on Facebook",
    "Add to Cart",
    "Copyright 2026 All rights reserved",
    "Products",
    "Our Products",
    "Specifications",
    "Cookies and Privacy Policy",
    "Subscribe to newsletter",
    "Sign in",
    "",
    "   ",
    "1234567890",
])
def test_rejects_non_products(line):
    assert _is_product_candidate(line) is False


@pytest.mark.parametrize("line", [
    "Stainless Steel Water Bottle 750 mL",
    "Insulated Steel Flask",
    "Industrial LED Light 100W",
    "Cotton T-Shirt (Bulk Pack)",
    "Aluminium Bottle 500ml",
    "Solar Panel 550W Monocrystalline",
    "BLDC Motor 24V 200W",
])
def test_accepts_real_products(line):
    assert _is_product_candidate(line) is True


def test_extract_products_ignores_noise_in_mixed_text():
    text = """
    MASTER CARTOON
    Stainless Steel Water Bottle 750 mL
    280 PCS IN SINGLE CARTOON
    ★★★★★ 4.8 (234)
    Insulated Steel Flask
    Share on Facebook
    """
    products = _extract_products(text, "https://example.com")
    lowered = [p.lower() for p in products]
    assert any("stainless steel water bottle" in p for p in lowered)
    assert any("insulated steel flask" in p for p in lowered)
    assert not any("master cartoon" in p for p in lowered)
    assert not any("response rate" in p for p in lowered)
    assert not any("★★★★★" in p for p in products)


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def test_confidence_zero_for_empty():
    assert _compute_confidence({}, {}) == 0.0


def test_confidence_scales_with_fields():
    low = _compute_confidence({"supplier_name": "X"}, {})
    mid = _compute_confidence(
        {"supplier_name": "X", "country": "India", "products": ["a"]},
        {},
    )
    high = _compute_confidence(
        {
            "supplier_name": "X", "country": "India", "supplier_type": "manufacturer",
            "products": ["a"], "moq": 100, "price": 2.5, "currency": "USD",
            "certifications": ["ISO 9001"], "email": "a@x.com", "phone": "+1",
        },
        {},
    )
    assert 0 < low < mid < high <= 1.0


def test_confidence_bounded_at_one():
    fields = {
        "supplier_name": "X", "country": "India", "supplier_type": "manufacturer",
        "products": ["a"], "moq": 100, "price": 2.5, "currency": "USD",
        "certifications": ["ISO"], "email": "a@x.com", "phone": "+1",
    }
    assert _compute_confidence(fields, {}) <= 1.0


# ---------------------------------------------------------------------------
# Completeness
# ---------------------------------------------------------------------------

def test_completeness_zero_for_empty():
    assert _compute_completeness({}) == 0.0


def test_completeness_counts_populated_fields():
    full = {
        "supplier_name": "X", "country": "India", "supplier_type": "manufacturer",
        "products": ["a"], "moq": 100, "price": 2.5, "currency": "USD",
        "certifications": ["ISO"], "email": "a@x.com", "phone": "+1",
    }
    assert _compute_completeness(full) == 1.0


def test_completeness_partial():
    partial = {"supplier_name": "X", "country": "India"}
    score = _compute_completeness(partial)
    assert 0.0 < score < 1.0


# ---------------------------------------------------------------------------
# End-to-end extraction
# ---------------------------------------------------------------------------

def test_extractor_populates_evidence():
    page = {
        "url": "https://acme.example/about",
        "title": "Acme Metals Pvt Ltd",
        "text": (
            "Acme Metals Pvt Ltd is a manufacturer of stainless steel water bottles. "
            "We are ISO 9001 certified and located in India. "
            "Contact: sales@acmemetals.com. MOQ 500 pieces. Price Rs 250 per piece."
        ),
    }
    result = DeterministicSupplierExtractor().extract(page)
    assert result.supplier_name is not None
    assert result.evidence, "evidence must be populated"
    assert "supplier_name" in result.evidence
    assert result.evidence["supplier_name"]["source_url"] == "https://acme.example/about"


def test_extractor_confidence_positive_when_fields_present():
    page = {
        "url": "https://acme.example/",
        "title": "Acme Metals Pvt Ltd - manufacturer",
        "text": "Acme Metals Pvt Ltd manufactures steel bottles in India. MOQ 100.",
    }
    result = DeterministicSupplierExtractor().extract(page)
    assert result.confidence > 0.0
    assert result.data_completeness > 0.0


def test_extractor_empty_page_zero_confidence():
    result = DeterministicSupplierExtractor().extract({"url": "https://x/"})
    assert result.confidence == 0.0
    assert result.data_completeness == 0.0


def test_extractor_records_supplier_type_signals():
    page = {
        "url": "https://x/",
        "title": "Factory Co",
        "text": "We are a manufacturer. Our factory produces goods.",
    }
    result = DeterministicSupplierExtractor().extract(page)
    assert result.supplier_type == "manufacturer"
    assert result.supplier_type_signals  # non-empty


# ---------------------------------------------------------------------------
# Normalizer — identity
# ---------------------------------------------------------------------------

def test_identity_key_uses_domain():
    s = {"website": "https://www.acme.example/about", "supplier_name": "Acme"}
    assert identity_key(s) == "domain:acme.example"


def test_identity_key_uses_email_domain_when_no_website():
    s = {"email": "sales@acme.example", "supplier_name": "Acme"}
    assert identity_key(s) == "emaildomain:acme.example"


def test_identity_key_uses_name_when_nothing_else():
    s = {"supplier_name": "Acme Metals"}
    key = identity_key(s)
    assert key is not None and key.startswith("name:")


def test_identity_key_none_when_no_signal():
    assert identity_key({}) is None
    assert identity_key({"supplier_name": "x"}) is None  # too short


# ---------------------------------------------------------------------------
# Normalizer — merge
# ---------------------------------------------------------------------------

def test_merge_prefers_non_empty():
    a = {"supplier_name": "Acme", "country": None}
    b = {"supplier_name": None, "country": "India"}
    merged = merge_records(a, b)
    assert merged["supplier_name"] == "Acme"
    assert merged["country"] == "India"


def test_merge_unions_lists():
    a = {"products": ["bottle", "flask"]}
    b = {"products": ["flask", "pump"]}
    merged = merge_records(a, b)
    assert sorted(merged["products"]) == ["bottle", "flask", "pump"]


def test_merge_keeps_max_confidence():
    a = {"confidence": 0.3}
    b = {"confidence": 0.7}
    assert merge_records(a, b)["confidence"] == 0.7


# ---------------------------------------------------------------------------
# Normalizer — dedup
# ---------------------------------------------------------------------------

def test_normalize_merges_same_domain():
    suppliers = [
        {"supplier_name": "Acme Metals", "website": "https://acme.example/a"},
        {"supplier_name": "ACME METALS PVT LTD", "website": "https://www.acme.example/b"},
    ]
    out = normalize_suppliers(suppliers)
    assert len(out) == 1


def test_normalize_does_not_merge_different_domains():
    suppliers = [
        {"supplier_name": "Acme", "website": "https://acme.example/"},
        {"supplier_name": "Beta", "website": "https://beta.example/"},
    ]
    out = normalize_suppliers(suppliers)
    assert len(out) == 2


def test_normalize_preserves_orphans():
    suppliers = [{"random": "value"}, {"another": "one"}]
    out = normalize_suppliers(suppliers)
    assert len(out) == 2


# ---------------------------------------------------------------------------
# Contradictions
# ---------------------------------------------------------------------------

def test_contradiction_detects_moq_mismatch():
    a = {"moq": 100, "source_urls": ["https://a/"]}
    b = {"moq": 500, "source_urls": ["https://b/"]}
    c = detect_contradictions(a, b)
    assert len(c) == 1
    assert c[0]["field"] == "moq"
    assert c[0]["value_a"] == 100
    assert c[0]["value_b"] == 500


def test_contradiction_ignores_matching_values():
    a = {"moq": 100}
    b = {"moq": 100}
    assert detect_contradictions(a, b) == []


def test_contradiction_ignores_missing_values():
    a = {"moq": 100}
    b = {}
    assert detect_contradictions(a, b) == []


def test_contradiction_case_insensitive_for_strings():
    a = {"country": "India"}
    b = {"country": "india"}
    assert detect_contradictions(a, b) == []


def test_detect_all_groups_by_identity():
    suppliers = [
        {"website": "https://acme.example/", "moq": 100, "source_urls": ["https://a/"]},
        {"website": "https://www.acme.example/", "moq": 500, "source_urls": ["https://b/"]},
        {"website": "https://beta.example/", "moq": 200},
    ]
    found = detect_all(suppliers)
    assert any(c["field"] == "moq" for c in found)
    assert all("identity" in c for c in found)