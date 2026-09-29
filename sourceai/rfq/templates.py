# sourceai/rfq/templates.py
"""
Deterministic RFQ and outreach templates.

No LLM. Same inputs always produce the same output.
Missing fields render as "[not specified]" — never fabricated.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


_MISSING = "[not specified]"

# Maximum rendered length for any template, to prevent a caller from
# accidentally generating a 100 KB email.
MAX_RENDERED_LENGTH = 8000


def _v(fields: Dict[str, Any], key: str) -> str:
    """Return the field value as a trimmed string, or the missing marker."""
    raw = fields.get(key)
    if raw is None:
        return _MISSING
    if isinstance(raw, str):
        s = raw.strip()
        return s if s else _MISSING
    if isinstance(raw, (list, tuple)):
        return ", ".join(str(x) for x in raw) if raw else _MISSING
    return str(raw)


def _clip(text: str) -> str:
    if len(text) <= MAX_RENDERED_LENGTH:
        return text
    return text[: MAX_RENDERED_LENGTH - 20] + "\n[... truncated ...]"


# ---------------------------------------------------------------------------
# RFQ
# ---------------------------------------------------------------------------

def render_rfq(fields: Dict[str, Any]) -> str:
    """
    Render a request-for-quote email body.

    Recognized fields:
      supplier, product, quantity, unit, moq, currency,
      spec, delivery_location, certifications, target_price, deadline
    """
    supplier = _v(fields, "supplier")
    product = _v(fields, "product")
    quantity = _v(fields, "quantity")
    unit = _v(fields, "unit")
    moq = _v(fields, "moq")
    currency = _v(fields, "currency")
    spec = _v(fields, "spec")
    delivery = _v(fields, "delivery_location")
    certifications = _v(fields, "certifications")
    target_price = _v(fields, "target_price")
    deadline = _v(fields, "deadline")

    lines = [
        f"Dear {supplier},",
        "",
        "We would like to request a quotation for the following:",
        "",
        f"Product: {product}",
        f"Quantity: {quantity} {unit}".rstrip(),
        f"Specifications: {spec}",
        f"Target MOQ: {moq}",
        f"Target unit price: {target_price} {currency}".rstrip(),
        f"Certifications required: {certifications}",
        f"Delivery location: {delivery}",
        f"Quote needed by: {deadline}",
        "",
        "Please include:",
        "  - Unit price and total price",
        "  - Minimum order quantity",
        "  - Production and shipping lead time",
        "  - Payment terms",
        "  - Certifications you can provide",
        "",
        "Thank you,",
    ]
    return _clip("\n".join(lines))


# ---------------------------------------------------------------------------
# Outreach
# ---------------------------------------------------------------------------

_OUTREACH_BUILDERS = {
    "initial": lambda f: _outreach_initial(f),
    "moq_inquiry": lambda f: _outreach_moq(f),
    "price_inquiry": lambda f: _outreach_price(f),
    "sample_request": lambda f: _outreach_sample(f),
    "follow_up": lambda f: _outreach_followup(f),
}

_OUTREACH_SUBJECTS = {
    "initial": "Inquiry: {product}",
    "moq_inquiry": "MOQ inquiry: {product}",
    "price_inquiry": "Price inquiry: {product}",
    "sample_request": "Sample request: {product}",
    "follow_up": "Following up: {product}",
}


def render_outreach(fields: Dict[str, Any], kind: str = "initial") -> str:
    """
    Render an outreach message. kind must be one of:
      initial | moq_inquiry | price_inquiry | sample_request | follow_up
    """
    if kind not in _OUTREACH_BUILDERS:
        raise ValueError(
            f"Unknown outreach kind: {kind!r}. "
            f"Valid: {sorted(_OUTREACH_BUILDERS)}"
        )
    return _clip(_OUTREACH_BUILDERS[kind](fields))


def render_subject(fields: Dict[str, Any], kind: str = "initial") -> str:
    template = _OUTREACH_SUBJECTS.get(kind, "Inquiry: {product}")
    return template.format(product=_v(fields, "product"))


# ---------------------------------------------------------------------------
# Individual outreach renderers
# ---------------------------------------------------------------------------

def _outreach_initial(f: Dict[str, Any]) -> str:
    return "\n".join([
        f"Dear {_v(f, 'supplier')},",
        "",
        f"We are sourcing {_v(f, 'product')} and came across your company.",
        "We would like to discuss a potential order.",
        "",
        f"Required quantity: {_v(f, 'quantity')} {_v(f, 'unit')}".rstrip(),
        f"Specifications: {_v(f, 'spec')}",
        f"Target price: {_v(f, 'target_price')} {_v(f, 'currency')}".rstrip(),
        "",
        "Could you share your product catalogue, MOQ, and pricing?",
        "",
        "Thank you,",
    ])


def _outreach_moq(f: Dict[str, Any]) -> str:
    return "\n".join([
        f"Dear {_v(f, 'supplier')},",
        "",
        f"Could you confirm your minimum order quantity (MOQ) for "
        f"{_v(f, 'product')}?",
        "",
        f"We are interested in ordering approximately "
        f"{_v(f, 'quantity')} {_v(f, 'unit')}.".rstrip(),
        "",
        "If the MOQ is higher than we can commit to initially, please let us "
        "know if there is flexibility for a trial order.",
        "",
        "Thank you,",
    ])


def _outreach_price(f: Dict[str, Any]) -> str:
    return "\n".join([
        f"Dear {_v(f, 'supplier')},",
        "",
        f"Could you provide a quotation for {_v(f, 'product')}?",
        "",
        f"Quantity: {_v(f, 'quantity')} {_v(f, 'unit')}".rstrip(),
        f"Specifications: {_v(f, 'spec')}",
        f"Target price: {_v(f, 'target_price')} {_v(f, 'currency')}".rstrip(),
        "",
        "Please include unit price, tiered pricing if available, and "
        "shipping terms.",
        "",
        "Thank you,",
    ])


def _outreach_sample(f: Dict[str, Any]) -> str:
    return "\n".join([
        f"Dear {_v(f, 'supplier')},",
        "",
        f"We would like to request a sample of {_v(f, 'product')}.",
        "",
        f"Specifications: {_v(f, 'spec')}",
        f"Delivery to: {_v(f, 'delivery_location')}",
        "",
        "Please let us know the sample cost, lead time, and any "
        "sample-fee refund policy for subsequent orders.",
        "",
        "Thank you,",
    ])


def _outreach_followup(f: Dict[str, Any]) -> str:
    return "\n".join([
        f"Dear {_v(f, 'supplier')},",
        "",
        f"I wanted to follow up on our earlier inquiry about "
        f"{_v(f, 'product')}.",
        "",
        "Have you had a chance to review our request? We are still "
        "interested and would appreciate an update.",
        "",
        "Thank you,",
    ])