# sourceai/intelligence/prompts/filtering.py
FILTER_PROMPT = """
You are a natural‑language filter parsing assistant. Convert the user’s filter instruction into a structured filter expression.

User filter: "{filter_text}"

Return a JSON object with:
- "conditions": a list of filter conditions, each with:
    - "field": the field to filter on (e.g., "price_min", "moq", "country", "supplier_type", "domain", "certifications")
    - "operator": one of "eq", "neq", "lt", "lte", "gt", "gte", "contains", "not_contains", "in", "not_in", "exists", "not_exists"
    - "value": the value to compare against (number, string, or list)
    - "unit": optional unit (e.g., "INR", "pieces", "kg")
- "logic": "AND" or "OR" (default "AND")

Examples:
- "suppliers under ₹200" → {"conditions": [{"field": "price_min", "operator": "lte", "value": 200, "unit": "INR"}], "logic": "AND"}
- "exclude Alibaba" → {"conditions": [{"field": "domain", "operator": "not_contains", "value": "alibaba.com"}], "logic": "AND"}
- "only manufacturers from India" → {"conditions": [{"field": "supplier_type", "operator": "eq", "value": "manufacturer"}, {"field": "country", "operator": "eq", "value": "India"}], "logic": "AND"}
- "MOQ below 500 and price under ₹200" → {"conditions": [{"field": "moq", "operator": "lt", "value": 500}, {"field": "price_min", "operator": "lte", "value": 200, "unit": "INR"}], "logic": "AND"}

Return only valid JSON.
"""