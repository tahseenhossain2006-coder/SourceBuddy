# sourceai/intelligence/prompts/missing_data.py
MISSING_DATA_PROMPT = """
You are a missing data reasoning assistant. Given a supplier's extracted data and optional source content, analyze why certain fields are missing and suggest actions to find them.

Context:
{context}

Return a JSON object with a "reasoning" list. Each item should contain:
- "field": the missing field name
- "reason": a short explanation of why it might be missing
- "importance": one of "critical", "important", "optional"
- "likely_source": where the information might be found (e.g., "product page", "supplier profile", "catalog", "contact page")
- "recommended_action": what the user should do to obtain this information

Example:
If price is missing, you might say:
{
  "reasoning": [
    {
      "field": "price",
      "reason": "Price may depend on order quantity or customization.",
      "importance": "critical",
      "likely_source": "quotation or product page",
      "recommended_action": "Request a quote from the supplier."
    }
  ]
}

Do not invent facts. Only reason based on the given context.
If the source content is insufficient, state that.
Return only valid JSON.
"""