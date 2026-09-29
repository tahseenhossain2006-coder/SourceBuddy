# sourceai/quote/comparator.py
from typing import List, Dict, Any
from sourceai.quote.models import QuoteResponse

class QuoteComparator:
    @staticmethod
    def compare(quotes: List[QuoteResponse]) -> Dict[str, Any]:
        if not quotes:
            return {}
        # Normalize currency (simplified: assume same currency)
        # Calculate effective price per unit (if moq provided)
        best_price = min(quotes, key=lambda q: q.price)
        best_moq = min(quotes, key=lambda q: q.moq if q.moq else float('inf'))
        fastest = min(quotes, key=lambda q: q.lead_time or '')
        # Overall recommendation (simplified)
        overall = best_price  # could use scoring
        return {
            "best_price": best_price.id,
            "best_moq": best_moq.id,
            "fastest": fastest.id,
            "overall_recommendation": overall.id,
            "comparison": [
                {
                    "supplier": q.supplier_id,
                    "price": q.price,
                    "moq": q.moq,
                    "lead_time": q.lead_time,
                    "payment_terms": q.payment_terms,
                }
                for q in quotes
            ]
        }