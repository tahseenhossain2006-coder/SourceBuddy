# sourceai/supplier/dedup.py
from typing import List, Dict
from urllib.parse import urlparse

def deduplicate_suppliers(suppliers: List[Dict]) -> List[Dict]:
    """Merge suppliers by domain or normalized name."""
    merged: Dict[str, Dict] = {}
    for s in suppliers:
        key = _canonical_key(s)
        if key not in merged:
            merged[key] = s
        else:
            merged[key] = _merge(merged[key], s)
    return list(merged.values())

def _canonical_key(s: Dict) -> str:
    website = s.get("website") or ""
    if website:
        try:
            return urlparse(website).netloc.lower().replace("www.", "")
        except Exception:
            pass
    name = (s.get("supplier_name") or "").lower()
    return "name:" + re.sub(r'\W+', '', name) if name else "unknown"

def _merge(a: Dict, b: Dict) -> Dict:
    out = dict(a)
    for k, v in b.items():
        if not out.get(k) and v:
            out[k] = v
        elif k == "evidence":
            out["evidence"] = {**(a.get("evidence") or {}), **(b.get("evidence") or {})}
    return out

import re