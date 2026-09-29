# sourceai/supplier/ranking.py
from typing import List, Dict, Any

def rank_suppliers(suppliers: List[Dict], constraints: Dict[str, Any]) -> List[Dict]:
    for s in suppliers:
        s["score"], s["ranking_reason"] = _score(s, constraints)
    return sorted(suppliers, key=lambda x: x["score"], reverse=True)

def _score(s: Dict, c: Dict) -> tuple:
    score = 0
    reasons = []
    # Constraint satisfaction
    if c.get("max_moq") and s.get("moq"):
        if s["moq"] <= c["max_moq"]:
            score += 20; reasons.append("MOQ within limit")
        else:
            score -= 30; reasons.append(f"MOQ {s['moq']} > {c['max_moq']}")
    if c.get("max_price") and s.get("price"):
        if s["price"] <= c["max_price"]:
            score += 20; reasons.append("Price within budget")
    if c.get("location") and s.get("country"):
        if c["location"].lower() in s["country"].lower():
            score += 15; reasons.append("Location matches")
    if c.get("supplier_type") and s.get("supplier_type") == c["supplier_type"]:
        score += 15; reasons.append("Supplier type matches")
    # Data completeness
    for f in ["website", "email", "phone", "whatsapp"]:
        if s.get(f):
            score += 5; reasons.append(f"Has {f}")
    # Evidence
    if s.get("evidence"):
        score += 10; reasons.append("Has evidence")
    # Confidence
    score += int((s.get("confidence") or 0) * 10)
    return score, "; ".join(reasons) or "No specific matches"