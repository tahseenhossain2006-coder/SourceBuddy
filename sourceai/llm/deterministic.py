# sourceai/llm/deterministic.py
"""
Deterministic supplier extraction.

No LLM. No network calls. Regex, keyword dictionaries, and HTML heuristics
only. Every extracted field carries per-field evidence (source URL +
snippet + method). Confidence is computed deterministically from field
coverage and evidence strength.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from sourceai.llm.structured import SupplierExtractionResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dictionaries
# ---------------------------------------------------------------------------

MANUFACTURER_TERMS = (
    "manufacturer", "manufacturing", "manufactures", "manufactured",
    "factory", "factories", "plant", "production facility",
    "oem", "odm", "producer", "produce", "produced",
)
WHOLESALER_TERMS = ("wholesaler", "wholesale", "bulk supplier", "bulk seller")
DISTRIBUTOR_TERMS = ("distributor", "distribution", "authorized dealer")
TRADER_TERMS = ("trader", "trading company", "trading co")
EXPORTER_TERMS = ("exporter", "export house", "exports", "exporting")
SUPPLIER_TERMS = ("supplier", "suppliers", "vendor", "sellers", "sellers of")
RETAILER_TERMS = ("retailer", "retail store", "shop")

CERT_PATTERNS = (
    r"\bISO\s?\d{4,5}(?::\d{4})?\b",
    r"\bISO\s?9001\b",
    r"\bISO\s?14001\b",
    r"\bCE\b",
    r"\bRoHS\b",
    r"\bREACH\b",
    r"\bFDA\b",
    r"\bBIS\b",
    r"\bHACCP\b",
    r"\bGMP\b",
    r"\bFSC\b",
    r"\bOEKO-TEX\b",
    r"\bASTM\s?[A-Z]?\d+\b",
)

# Product noun dictionary — required for a line to be considered a product.
# This is what prevents "MASTER CARTOON" and "82% Response Rate" from
# being classified as products.
PRODUCT_NOUNS = {
    "bottle", "flask", "container", "box", "bag", "pump", "motor", "valve",
    "pipe", "fitting", "sheet", "plate", "rod", "wire", "cable", "light",
    "lamp", "led", "solar", "panel", "battery", "charger", "adapter",
    "transformer", "sensor", "controller", "display", "screen", "monitor",
    "fan", "cooler", "heater", "radiator", "filter", "tank", "drum",
    "screw", "bolt", "nut", "washer", "bearing", "gear", "belt", "chain",
    "spring", "seal", "gasket", "clamp", "bracket", "hinge", "lock",
    "handle", "knob", "button", "switch", "socket", "plug", "connector",
    "cable", "harness", "insulator", "conductor", "resistor", "capacitor",
    "diode", "transistor", "relay", "fuse", "circuit", "board", "chip",
    "textile", "fabric", "cloth", "shirt", "pant", "tshirt", "t-shirt",
    "dress", "jacket", "coat", "sweater", "sock", "shoe", "bag", "cap",
    "chair", "table", "desk", "bed", "sofa", "cabinet", "shelf", "rack",
    "bottle", "cup", "mug", "glass", "plate", "bowl", "spoon", "fork",
    "knife", "tray", "pot", "pan", "kettle", "cutlery", "utensil",
    "machine", "equipment", "tool", "device", "instrument", "apparatus",
    "module", "unit", "assembly", "component", "part", "kit", "set",
    "rope", "thread", "string", "twine", "webbing", "net", "mesh",
    "paint", "coating", "adhesive", "glue", "tape", "film", "foil",
    "cement", "concrete", "brick", "block", "tile", "stone", "sand",
    "insulation", "membrane", "barrier", "liner", "mat", "pad",
    "paper", "cardboard", "carton", "envelope", "label", "sticker",
    "pen", "pencil", "marker", "notebook", "folder", "file", "clip",
    "food", "snack", "beverage", "drink", "juice", "water", "oil", "sauce",
    "spice", "grain", "flour", "sugar", "salt", "tea", "coffee", "cocoa",
    "medicine", "tablet", "capsule", "syrup", "cream", "ointment", "lotion",
    "cosmetic", "shampoo", "soap", "detergent", "cleaner", "polish",
}

# Patterns that immediately disqualify a candidate product line.
_PRODUCT_REJECT = [
    re.compile(r"^\s*\d+\s*(?:%|pcs?|pieces?|units?|cartons?|boxes?|kg|g|lb)\b", re.I),
    re.compile(r"\bresponse\s+rate\b", re.I),
    re.compile(r"[★☆⭐]+"),
    re.compile(r"^\s*[\W\d_]+\s*$"),
    re.compile(r"\b(?:copyright|all rights reserved|privacy|terms of (?:use|service))\b", re.I),
    re.compile(r"^\s*(?:home|about|contact|sign\s*in|log\s*in|sign\s*up|register)\s*$", re.I),
    re.compile(r"\b(?:subscribe|newsletter|menu|cookie|cart|checkout)\b", re.I),
    re.compile(r"^\s*(?:share|tweet|like|follow|pin)\s+", re.I),
    re.compile(r"^\s*\d+\s*(?:st|nd|rd|th)\s+", re.I),
    re.compile(r"\b(?:add\s+to\s+(?:cart|wishlist)|buy\s+now)\b", re.I),
    re.compile(r"^\s*[\d\s\-/]+\s*$"),   # pure date/number lines
]

# Words that make a line look like a heading, not a product.
_HEADING_PREFIXES = (
    "products", "our products", "product range", "categories", "category",
    "specifications", "features", "description", "details", "overview",
    "related", "recommended", "similar", "you may also", "customers",
    "faq", "frequently asked", "contact us", "get in touch", "about us",
)


# ---------------------------------------------------------------------------
# Currency
# ---------------------------------------------------------------------------

CURRENCY_SYMBOLS = {
    "₹": "INR", "Rs": "INR", "Rs.": "INR", "INR": "INR",
    "$": "USD", "USD": "USD", "US$": "USD",
    "€": "EUR", "EUR": "EUR",
    "£": "GBP", "GBP": "GBP",
    "¥": "CNY", "CNY": "CNY", "RMB": "CNY",
    "৳": "BDT", "BDT": "BDT",
}

COUNTRY_NAMES = (
    "India", "China", "Bangladesh", "Vietnam", "Indonesia", "Thailand",
    "Malaysia", "Singapore", "Sri Lanka", "Pakistan", "Nepal",
    "United States", "USA", "United Kingdom", "UK", "Germany", "France",
    "Italy", "Spain", "Netherlands", "Poland", "Turkey", "Russia",
    "Brazil", "Mexico", "Canada", "Australia", "Japan", "South Korea",
    "Taiwan", "UAE", "United Arab Emirates", "Saudi Arabia",
)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(
    r"(?:(?:\+|00)\d{1,3}[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}"
)
MOQ_RE = re.compile(
    r"(?:MOQ|minimum\s+order(?:\s+quantity)?|min\.?\s*order|minimum\s+quantity)"
    r"[^\d]{0,20}(\d[\d,\.]*)",
    re.IGNORECASE,
)
PRICE_RE = re.compile(
    r"(₹|Rs\.?|INR|\$|USD|US\$|€|EUR|£|GBP|¥|CNY|RMB)\s?([\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _first_country(text: str) -> Optional[str]:
    lower = text.lower()
    for name in COUNTRY_NAMES:
        if re.search(r"\b" + re.escape(name.lower()) + r"\b", lower):
            return name
    return None


def _detect_supplier_type(text: str) -> Tuple[Optional[str], List[str]]:
    """
    Return (type, signals) where signals are the literal terms found in text.
    Signals are evidence for why the classification was made.
    """
    lower = text.lower()
    groups = {
        "manufacturer": MANUFACTURER_TERMS,
        "wholesaler": WHOLESALER_TERMS,
        "distributor": DISTRIBUTOR_TERMS,
        "trader": TRADER_TERMS,
        "exporter": EXPORTER_TERMS,
        "supplier": SUPPLIER_TERMS,
        "retailer": RETAILER_TERMS,
    }
    scores: Dict[str, int] = {}
    signals: Dict[str, List[str]] = {}
    for label, terms in groups.items():
        hits = [t for t in terms if t in lower]
        scores[label] = len(hits)
        signals[label] = hits

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return None, []
    return best, signals[best][:5]


def _detect_certifications(text: str) -> List[str]:
    found: List[str] = []
    for pattern in CERT_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            val = match.group(0).strip().upper()
            if val not in found:
                found.append(val)
    return found[:20]


def _extract_moq(text: str) -> Optional[int]:
    m = MOQ_RE.search(text)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", "").replace(".", ""))
    except ValueError:
        return None


def _extract_price(text: str) -> Tuple[Optional[float], Optional[str]]:
    m = PRICE_RE.search(text)
    if not m:
        return None, None
    symbol, num = m.group(1), m.group(2)
    try:
        price = float(num.replace(",", ""))
    except ValueError:
        return None, None
    currency = CURRENCY_SYMBOLS.get(symbol.upper(), CURRENCY_SYMBOLS.get(symbol))
    return price, currency


def _is_product_candidate(line: str) -> bool:
    """Return True if a line looks like a product, not page furniture."""
    s = _clean(line)
    if not (8 <= len(s) <= 120):
        return False

    # Reject patterns that never signal a product
    for pat in _PRODUCT_REJECT:
        if pat.search(s):
            return False

    # Reject headings
    low = s.lower()
    for prefix in _HEADING_PREFIXES:
        if low.startswith(prefix):
            return False

    # Require at least one product noun (whole-word match)
    tokens = re.findall(r"[a-z]+", low)
    if not any(tok in PRODUCT_NOUNS for tok in tokens):
        return False

    # Reject lines with excessive numeric content (rating widgets, tables)
    digits = sum(c.isdigit() for c in s)
    if digits > len(s) * 0.5:
        return False

    # Reject lines with too many symbols (bullets, stars, symbols)
    symbols = sum(1 for c in s if not c.isalnum() and not c.isspace())
    if symbols > len(s) * 0.3:
        return False

    return True


def _extract_products(text: str, url: str) -> List[str]:
    """
    Extract short candidate product phrases.

    Stricter than v1: requires a product noun, rejects headings, rating
    widgets, navigation, and symbol-heavy lines.
    """
    # Split into lines first — bullet separators second
    raw_lines = re.split(r"[\n\r]+", text)
    candidates: List[str] = []

    for raw_line in raw_lines:
        # Further split bullet lists within a line
        for part in re.split(r"[•·\|]+", raw_line):
            s = _clean(part)
            if _is_product_candidate(s):
                candidates.append(s)
                if len(candidates) >= 40:
                    break
        if len(candidates) >= 40:
            break

    # Dedupe preserving order
    seen = set()
    out: List[str] = []
    for c in candidates:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out[:20]


def _extract_name(text: str, url: str, title: str) -> Optional[str]:
    if title:
        cleaned = re.split(r"[|\-–—]", title)[0].strip()
        if 3 <= len(cleaned) <= 80 and re.search(
            r"(pvt|private|limited|ltd|inc|llc|corp|corporation|co\.|company|"
            r"industries|enterprises|trading|exports|manufactur)",
            cleaned, re.IGNORECASE,
        ):
            return cleaned

    m = re.search(
        r"([A-Z][A-Za-z0-9&.,'\- ]{2,60}"
        r"(?:Pvt\.?\s*Ltd\.?|Private\s+Limited|Limited|Ltd\.?|Inc\.?|LLC|Corp\.?|"
        r"Industries|Enterprises|Trading|Exports|Manufacturing|Manufacturers))",
        text,
    )
    if m:
        return _clean(m.group(1))

    return None


def _snippet(text: str, match: str, window: int = 60) -> str:
    """Return a short window around the first occurrence of `match`."""
    if not match:
        return ""
    idx = text.find(match)
    if idx < 0:
        return match[:120]
    start = max(0, idx - window)
    end = min(len(text), idx + len(match) + window)
    return _clean(text[start:end])


# ---------------------------------------------------------------------------
# Evidence + confidence
# ---------------------------------------------------------------------------

_FIELD_WEIGHTS = {
    "supplier_name": 2.0,
    "country": 1.0,
    "supplier_type": 1.5,
    "products": 1.5,
    "moq": 1.5,
    "price": 1.5,
    "currency": 0.5,
    "certifications": 1.0,
    "email": 1.5,
    "phone": 1.0,
}

_FIELD_ORDER = list(_FIELD_WEIGHTS.keys())


def _build_evidence(
    text: str,
    url: str,
    fields: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Produce per-field evidence: value, source URL, snippet, extraction method.
    Only fields with a non-empty value get evidence.
    """
    evidence: Dict[str, Dict[str, Any]] = {}
    for field, value in fields.items():
        if value in (None, "", [], {}):
            continue
        # Pick a representative snippet to search for
        if isinstance(value, list):
            snippet_src = value[0] if value else ""
        else:
            snippet_src = str(value)
        evidence[field] = {
            "value": value,
            "source_url": url,
            "snippet": _snippet(text, snippet_src),
            "method": "regex",
            "confidence": 0.7,   # per-field confidence; see _compute_confidence
        }
    return evidence


def _compute_confidence(
    fields: Dict[str, Any],
    evidence: Dict[str, Any],
) -> float:
    """
    Deterministic confidence: weighted field coverage in [0, 1].

    A supplier with name + country + supplier_type + 1 product + MOQ scores
    higher than a supplier with only a name. No field present → 0.0.
    """
    total_weight = sum(_FIELD_WEIGHTS.values())
    earned = 0.0
    for field, weight in _FIELD_WEIGHTS.items():
        if fields.get(field) not in (None, "", [], {}):
            earned += weight
    if total_weight == 0:
        return 0.0
    return round(min(1.0, earned / total_weight), 3)


def _compute_completeness(fields: Dict[str, Any]) -> float:
    """Fraction of expected fields that are populated."""
    expected = [
        "supplier_name", "country", "supplier_type", "products",
        "moq", "price", "currency", "certifications", "email", "phone",
    ]
    present = sum(1 for f in expected if fields.get(f) not in (None, "", [], {}))
    return round(present / len(expected), 3)


# ---------------------------------------------------------------------------
# Public extractor
# ---------------------------------------------------------------------------

class DeterministicSupplierExtractor:
    """
    Deterministic supplier extraction.

    Same public surface as the LLM path in LLMIntegration so callers can
    swap implementations transparently.
    """

    def extract(self, page: Dict[str, Any]) -> SupplierExtractionResult:
        text = page.get("text") or ""
        title = page.get("title") or ""
        url = page.get("url") or ""

        if not text and not title:
            return SupplierExtractionResult(source_urls=[url] if url else [])

        name = _extract_name(text, url, title)
        country = _first_country(text)
        supplier_type, type_signals = _detect_supplier_type(text)
        certifications = _detect_certifications(text)
        moq = _extract_moq(text)
        price, currency = _extract_price(text)

        emails = list({e.lower() for e in EMAIL_RE.findall(text)})[:3]
        phones = [
            p.strip() for p in PHONE_RE.findall(text)
            if len(p.strip()) >= 8
        ][:3]

        products = _extract_products(text, url)

        fields: Dict[str, Any] = {
            "supplier_name": name,
            "country": country,
            "supplier_type": supplier_type,
            "products": products[:20],
            "moq": moq,
            "price": price,
            "currency": currency,
            "certifications": certifications,
            "email": emails[0] if emails else None,
            "phone": phones[0] if phones else None,
        }

        evidence = _build_evidence(text, url, fields)
        confidence = _compute_confidence(fields, evidence)
        completeness = _compute_completeness(fields)

        return SupplierExtractionResult(
            supplier_name=name,
            company_name=name,
            website=None,
            country=country,
            supplier_type=supplier_type,
            supplier_type_signals=type_signals,
            products=products[:20],
            moq=moq,
            price=price,
            currency=currency,
            certifications=certifications,
            email=emails[0] if emails else None,
            phone=phones[0] if phones else None,
            source_urls=[url] if url else [],
            evidence=evidence,
            data_completeness=completeness,
            confidence=confidence,
        )

    def extract_batch(
        self, pages: List[Dict[str, Any]]
    ) -> List[SupplierExtractionResult]:
        out: List[SupplierExtractionResult] = []
        for page in pages:
            try:
                out.append(self.extract(page))
            except Exception as exc:
                logger.warning(
                    "Deterministic extraction failed for %s: %s",
                    page.get("url", "unknown"), exc,
                )
        return out