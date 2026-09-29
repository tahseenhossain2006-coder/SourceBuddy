# sourceai/supplier/contradictions.py
"""
Deterministic contradiction detection.

Given two supplier records that share an identity, compare a fixed set of
scalar fields. When both records have a non-empty value and the values
differ, emit a contradiction record.

No winner is chosen automatically — the caller decides using source
priority rules.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

COMPARABLE_FIELDS = (
    "supplier_name", "country", "state", "city",
    "supplier_type", "moq", "price", "currency",
)


def _values_differ(a: Any, b: Any) -> bool:
    """Loose comparison: trim strings, compare case-insensitively for text."""
    if a is None or b is None:
        return False
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() != b.strip().lower()
    return a != b


def detect_contradictions(
    a: Dict[str, Any],
    b: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Return a list of contradiction records between two supplier dicts.

    Each record:
      {
        "field": "moq",
        "value_a": 100,
        "value_b": 500,
        "source_a": "<url from a>",
        "source_b": "<url from b>",
        "conflict_type": "value_mismatch",
      }
    """
    contradictions: List[Dict[str, Any]] = []

    src_a = (a.get("source_urls") or [None])[0]
    src_b = (b.get("source_urls") or [None])[0]

    for field in COMPARABLE_FIELDS:
        va = a.get(field)
        vb = b.get(field)
        if va in (None, "", [], {}) or vb in (None, "", [], {}):
            continue
        if _values_differ(va, vb):
            contradictions.append({
                "field": field,
                "value_a": va,
                "value_b": vb,
                "source_a": src_a,
                "source_b": src_b,
                "conflict_type": "value_mismatch",
            })

    return contradictions


def detect_all(
    suppliers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Given a list of supplier dicts that have already been grouped by
    identity, compare each pair and collect all contradictions.
    """
    from sourceai.supplier.normalizer import identity_key

    by_identity: Dict[str, List[Dict[str, Any]]] = {}
    for s in suppliers:
        key = identity_key(s)
        if key is None:
            continue
        by_identity.setdefault(key, []).append(s)

    out: List[Dict[str, Any]] = []
    for key, group in by_identity.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                for c in detect_contradictions(group[i], group[j]):
                    c["identity"] = key
                    out.append(c)
    return out