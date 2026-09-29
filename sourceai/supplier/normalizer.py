# sourceai/supplier/normalizer.py
"""
Cross-source supplier normalization.

Merges duplicate supplier records found across multiple pages.
Uses domain, normalized name, and email domain as identity keys.
Never merges based on name similarity alone.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Legal-form suffixes to strip when comparing names.
_LEGAL_SUFFIXES = (
    "pvt ltd", "pvt. ltd.", "private limited", "ltd", "ltd.", "limited",
    "inc", "inc.", "llc", "corp", "corp.", "corporation", "co.",
    "gmbh", "s.a.", "s.a", "b.v.", "b.v", "pty ltd",
)


def _normalize_name(name: Optional[str]) -> str:
    """
    Lowercase, strip legal suffix, strip punctuation, collapse spaces.
    Used only as a *secondary* identity key — never primary.
    """
    if not name:
        return ""
    s = name.lower().strip()
    for suffix in _LEGAL_SUFFIXES:
        if s.endswith(" " + suffix):
            s = s[: -len(suffix) - 1].strip()
        elif s.endswith(suffix):
            s = s[: -len(suffix)].strip()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _domain_of(url: Optional[str]) -> str:
    if not url:
        return ""
    try:
        p = urlparse(url)
        netloc = (p.netloc or "").lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def _email_domain(email: Optional[str]) -> str:
    if not email or "@" not in email:
        return ""
    return email.split("@", 1)[1].lower().strip()


def identity_key(supplier: Dict[str, Any]) -> Optional[str]:
    """
    Return a canonical identity key for a supplier dict, or None if no
    reliable identity signal exists.

    Priority:
      1. Domain of primary website
      2. Domain of email
      3. Normalized company name (weakest — used only if 1 and 2 absent)
    """
    domain = _domain_of(supplier.get("website"))
    if domain:
        return f"domain:{domain}"

    ed = _email_domain(supplier.get("email"))
    if ed and ed not in ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com"):
        return f"emaildomain:{ed}"

    name = _normalize_name(
        supplier.get("supplier_name") or supplier.get("company_name")
    )
    if len(name) >= 5:
        return f"name:{name}"

    return None


def merge_records(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two supplier dicts that share an identity.

    Rules:
      - Non-empty values win over empty ones.
      - Lists are unioned without duplicates.
      - Confidences are combined as max (the stronger evidence wins).
      - Source URLs are unioned.
    """
    merged = dict(a)

    for key, bval in b.items():
        aval = merged.get(key)

        if isinstance(aval, list) and isinstance(bval, list):
            seen = set()
            out: List[Any] = []
            for x in aval + bval:
                k = str(x)
                if k not in seen:
                    seen.add(k)
                    out.append(x)
            merged[key] = out

        elif isinstance(aval, dict) and isinstance(bval, dict):
            combined = dict(aval)
            for k, v in bval.items():
                combined.setdefault(k, v)
            merged[key] = combined

        elif aval in (None, "", 0, 0.0) and bval not in (None, "", 0, 0.0):
            merged[key] = bval

        elif key == "confidence" and isinstance(bval, (int, float)):
            merged[key] = max(float(aval or 0), float(bval))

    return merged


def normalize_suppliers(
    suppliers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Deduplicate a list of supplier dicts by identity key.

    Suppliers without an identity key are preserved as-is (never merged
    with anything, since we can't prove they're the same).
    """
    buckets: Dict[str, Dict[str, Any]] = {}
    orphans: List[Dict[str, Any]] = []

    for s in suppliers:
        key = identity_key(s)
        if key is None:
            orphans.append(s)
            continue
        if key in buckets:
            buckets[key] = merge_records(buckets[key], s)
        else:
            buckets[key] = dict(s)

    return list(buckets.values()) + orphans