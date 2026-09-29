# sourceai/supplier/intelligence.py
import re
from typing import Dict, Any, Optional

def normalize_supplier(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize an extracted supplier into the canonical schema."""
    return {
        "supplier_name": raw.get("company_name") or raw.get("supplier_name"),
        "supplier_type": _classify_type(raw),
        "product": raw.get("product"),
        "moq": _to_int(raw.get("moq")),
        "moq_unit": raw.get("moq_unit"),
        "price": _to_float(raw.get("price")),
        "currency": raw.get("currency"),
        "price_unit": raw.get("price_unit"),
        "location": raw.get("location"),
        "country": raw.get("country"),
        "website": raw.get("website"),
        "email": raw.get("email"),
        "phone": raw.get("phone"),
        "whatsapp": raw.get("whatsapp"),
        "certifications": raw.get("certifications") or [],
        "evidence": raw.get("evidence") or {},
        "confidence": raw.get("confidence", 0.0),
    }

def _classify_type(raw: Dict[str, Any]) -> Optional[str]:
    text = (str(raw.get("supplier_type", "")) + " " +
            str(raw.get("company_name", "")) + " " +
            str(raw.get("text", ""))).lower()
    for t, kws in [
        ("manufacturer", ["manufacturer", "factory", "producer"]),
        ("distributor", ["distributor", "distributor company"]),
        ("wholesaler", ["wholesaler", "wholesale"]),
        ("trader", ["trader", "trading"]),
        ("retailer", ["retailer", "retail"]),
    ]:
        for kw in kws:
            if kw in text:
                return t
    return "unknown"

def _to_int(v) -> Optional[int]:
    if v is None: return None
    try:
        m = re.search(r'\d+', str(v).replace(",", ""))
        return int(m.group(0)) if m else None
    except Exception:
        return None

def _to_float(v) -> Optional[float]:
    if v is None: return None
    try:
        m = re.search(r'\d+(\.\d+)?', str(v).replace(",", ""))
        return float(m.group(0)) if m else None
    except Exception:
        return None