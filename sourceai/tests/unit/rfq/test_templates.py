"""RFQ + outreach template tests."""
import pytest

from sourceai.rfq.templates import (
    render_rfq,
    render_outreach,
    render_subject,
    MAX_RENDERED_LENGTH,
)


BASE = {
    "supplier": "Acme Metals",
    "product": "Stainless steel water bottle",
    "quantity": 1000,
    "unit": "pcs",
    "moq": 500,
    "currency": "USD",
    "spec": "500ml, insulated",
    "delivery_location": "Kolkata, India",
    "certifications": "ISO 9001, CE",
    "target_price": 2.50,
    "deadline": "2026-10-15",
}


# ---------------------------------------------------------------------------
# RFQ
# ---------------------------------------------------------------------------

def test_rfq_contains_all_fields():
    text = render_rfq(BASE)
    assert "Acme Metals" in text
    assert "Stainless steel water bottle" in text
    assert "1000" in text
    assert "500ml, insulated" in text
    assert "Kolkata, India" in text
    assert "ISO 9001, CE" in text
    assert "2.5" in text
    assert "USD" in text


def test_rfq_missing_fields_render_marker():
    text = render_rfq({})
    assert "[not specified]" in text
    # Must not fabricate any concrete value
    assert "Acme" not in text


def test_rfq_is_deterministic():
    assert render_rfq(BASE) == render_rfq(BASE)


def test_rfq_handles_non_ascii():
    fields = dict(BASE, currency="₹", target_price=200)
    text = render_rfq(fields)
    assert "₹" in text
    assert "200" in text


def test_rfq_clips_oversized_input():
    huge = {"spec": "x" * 100_000}
    text = render_rfq(huge)
    assert len(text) <= MAX_RENDERED_LENGTH


# ---------------------------------------------------------------------------
# Outreach
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", [
    "initial", "moq_inquiry", "price_inquiry",
    "sample_request", "follow_up",
])
def test_outreach_kinds_render(kind):
    text = render_outreach(BASE, kind)
    assert isinstance(text, str)
    assert len(text) > 0
    assert "Acme Metals" in text


def test_outreach_unknown_kind_raises():
    with pytest.raises(ValueError):
        render_outreach(BASE, "not_a_kind")


def test_outreach_missing_fields_do_not_crash():
    for kind in ("initial", "moq_inquiry", "price_inquiry",
                 "sample_request", "follow_up"):
        text = render_outreach({}, kind)
        assert "[not specified]" in text


def test_subject_uses_product_name():
    subject = render_subject(BASE, "initial")
    assert "Stainless steel water bottle" in subject


def test_subject_missing_product_uses_marker():
    subject = render_subject({}, "initial")
    assert "[not specified]" in subject