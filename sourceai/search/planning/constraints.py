# sourceai/search/planning/constraints.py
import re
from typing import Any, Dict


class ConstraintExtractor:
    """
    Deterministic extraction of MOQ, price, and currency from a query.

    The MOQ pattern runs first. Price detection requires an explicit
    price context word (price, cost, budget, rate, under, below, less
    than, at most, <=), so a bare number is not misread as a price.
    """

    # Match: MOQ keyword, optional separator (":" "=" "-"), optional
    # comparator, the number, optional unit.
    _moq_pattern = re.compile(
        r'(?:moq|minimum\s*(?:order\s*)?(?:quantity)?)'
        r'\s*[:=\-]?\s*'
        r'(?:under|below|less\s*than|at\s*most|<=|≤|:|=)?\s*'
        r'([\d,]+)',
        re.I,
    )

    # Match: explicit price keyword (REQUIRED) then comparator/number.
    # The keyword is NOT optional — that is what prevents "MOQ 500"
    # from being read as a price.
    _price_pattern = re.compile(
        r'(?:price|cost|budget|rate|under|below|less\s*than|at\s*most|max(?:imum)?|<=|≤)'
        r'\s*[:=\-]?\s*'
        r'([\d,]+(?:\.\d+)?)\s*'
        r'(usd|inr|eur|gbp|cny|rmb|¥|₹|€|£|\$)?',
        re.I,
    )

    # Currency-symbol-prefix form: "$5", "₹200", "€10"
    _currency_symbol_pattern = re.compile(
        r'([€\$¥₹£])\s*([\d,]+(?:\.\d+)?)',
        re.I,
    )

    # ISO code prefix form: "USD 5", "INR 200"
    _currency_code_pattern = re.compile(
        r'\b(usd|inr|eur|gbp|cny|rmb)\s*([\d,]+(?:\.\d+)?)',
        re.I,
    )

    _currency_map = {
        'usd': 'USD', 'dollar': 'USD', '$': 'USD',
        'inr': 'INR', 'rupee': 'INR', '₹': 'INR',
        'eur': 'EUR', 'euro': 'EUR', '€': 'EUR',
        'gbp': 'GBP', 'pound': 'GBP', '£': 'GBP',
        'cny': 'CNY', 'rmb': 'CNY', '¥': 'CNY',
    }

    _moq_unit_pattern = re.compile(
        r'\b(pieces?|units?|pcs?|kg|kgs|g|grams?|liters?|litres?|'
        r'boxes?|cases?|cartons?|sets?)\b',
        re.I,
    )

    @classmethod
    def extract(cls, query: str) -> Dict[str, Any]:
        constraints: Dict[str, Any] = {}

        # ---- MOQ (runs first) ----
        moq_match = cls._moq_pattern.search(query)
        if moq_match:
            raw = moq_match.group(1)
            if raw:
                try:
                    constraints["max_moq"] = int(raw.replace(",", ""))
                except ValueError:
                    pass
            unit_match = cls._moq_unit_pattern.search(query)
            constraints["moq_unit"] = (
                unit_match.group(1).lower() if unit_match else "pieces"
            )

        # ---- Price ----
        price_match = cls._price_pattern.search(query)
        if price_match:
            raw = price_match.group(1)
            if raw:
                try:
                    constraints["max_price"] = float(raw.replace(",", ""))
                except ValueError:
                    pass
            if price_match.group(2):
                curr = price_match.group(2).lower()
                if curr in cls._currency_map:
                    constraints["currency"] = cls._currency_map[curr]

        # ---- Currency-symbol prefix ----
        if "max_price" not in constraints:
            sym_match = cls._currency_symbol_pattern.search(query)
            if sym_match:
                symbol, raw = sym_match.group(1), sym_match.group(2)
                if raw:
                    try:
                        constraints["max_price"] = float(raw.replace(",", ""))
                    except ValueError:
                        pass
                if symbol in cls._currency_map:
                    constraints["currency"] = cls._currency_map[symbol]

        # ---- ISO code prefix (e.g. "USD 5") ----
        if "max_price" not in constraints:
            code_match = cls._currency_code_pattern.search(query)
            if code_match:
                code, raw = code_match.group(1), code_match.group(2)
                if raw:
                    try:
                        constraints["max_price"] = float(raw.replace(",", ""))
                    except ValueError:
                        pass
                if code.lower() in cls._currency_map:
                    constraints["currency"] = cls._currency_map[code.lower()]

        # ---- Standalone currency code anywhere ----
        if "currency" not in constraints:
            for sym, code in cls._currency_map.items():
                if re.search(r'\b' + re.escape(sym) + r'\b', query, re.I) or \
                   sym in query:
                    constraints["currency"] = code
                    break

        return constraints