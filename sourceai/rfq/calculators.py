# sourceai/rfq/calculators.py
"""
Deterministic procurement calculators.

Every function is pure and returns a dict with at least:
  - value (or None)
  - unit (str)
  - currency (str, when money is involved)
  - reason (str, human-readable)
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def _num(value: Any) -> Optional[float]:
    """Coerce to float, tolerating None/str. Returns None on failure."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def unit_times_quantity(
    unit_price: float,
    quantity: int,
    currency: str = "USD",
) -> Dict[str, Any]:
    up = _num(unit_price)
    q = _num(quantity)
    if up is None or q is None:
        return {"value": None, "unit": "total", "currency": currency,
                "reason": "Invalid unit_price or quantity"}
    if up < 0 or q < 0:
        return {"value": None, "unit": "total", "currency": currency,
                "reason": "Negative values not allowed"}
    total = up * q
    return {
        "value": round(total, 2),
        "unit": "total",
        "currency": currency,
        "reason": f"{up} × {int(q)} = {round(total, 2)} {currency}",
    }


def moq_feasibility(requested_qty: int, moq: int) -> Dict[str, Any]:
    rq = _num(requested_qty)
    mq = _num(moq)
    if rq is None or mq is None:
        return {"value": None, "unit": "units", "feasible": False,
                "reason": "Invalid requested_qty or moq"}
    if mq <= 0:
        # No MOQ constraint — any requested quantity is feasible.
        return {"value": 0, "unit": "units", "feasible": True,
                "reason": "No MOQ constraint"}
    feasible = rq >= mq
    shortfall = max(0, int(mq - rq))
    return {
        "value": shortfall,
        "unit": "units",
        "feasible": feasible,
        "reason": (
            f"Meets MOQ ({int(rq)} >= {int(mq)})"
            if feasible
            else f"Short by {shortfall} units"
        ),
    }

def budget_feasibility(
    unit_price: float,
    quantity: int,
    budget: float,
    currency: str = "USD",
) -> Dict[str, Any]:
    up = _num(unit_price)
    q = _num(quantity)
    b = _num(budget)
    if up is None or q is None or b is None:
        return {"value": None, "currency": currency,
                "reason": "Invalid inputs"}
    if up < 0 or q < 0 or b < 0:
        return {"value": None, "currency": currency,
                "reason": "Negative values not allowed"}
    total = up * q
    feasible = total <= b
    over = max(0, round(total - b, 2))
    return {
        "value": round(over, 2),
        "currency": currency,
        "total": round(total, 2),
        "budget": round(b, 2),
        "feasible": feasible,
        "reason": (
            f"Within budget ({round(total, 2)} <= {round(b, 2)} {currency})"
            if feasible
            else f"Over budget by {over} {currency}"
        ),
    }


def total_quoted_cost(
    unit_price: float,
    quantity: int,
    shipping: float = 0.0,
    currency: str = "USD",
) -> Dict[str, Any]:
    up = _num(unit_price)
    q = _num(quantity)
    sh = _num(shipping) or 0.0
    if up is None or q is None:
        return {"value": None, "currency": currency,
                "reason": "Invalid unit_price or quantity"}
    total = up * q + sh
    return {
        "value": round(total, 2),
        "currency": currency,
        "reason": f"{up} × {int(q)} + {sh} shipping = {round(total, 2)} {currency}",
    }


def price_per_unit(total: float, quantity: int, currency: str = "USD") -> Dict[str, Any]:
    t = _num(total)
    q = _num(quantity)
    if t is None or q is None:
        return {"value": None, "currency": currency, "reason": "Invalid inputs"}
    if q <= 0:
        return {"value": None, "currency": currency,
                "reason": "Quantity must be positive"}
    return {
        "value": round(t / q, 4),
        "currency": currency,
        "reason": f"{t} / {int(q)} = {round(t / q, 4)} {currency}/unit",
    }


def quantity_difference(requested: int, available: int) -> Dict[str, Any]:
    rq = _num(requested)
    av = _num(available)
    if rq is None or av is None:
        return {"value": None, "unit": "units",
                "reason": "Invalid inputs"}
    diff = int(av - rq)
    return {
        "value": diff,
        "unit": "units",
        "reason": (
            f"Available exceeds request by {diff}"
            if diff > 0
            else f"Request exceeds available by {-diff}"
            if diff < 0
            else "Exactly matches"
        ),
    }