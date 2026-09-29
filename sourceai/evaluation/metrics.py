# sourceai/evaluation/metrics.py
from typing import List, Dict, Any
from collections import Counter

def compute_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute evaluation metrics from a list of test cases.

    Each result should contain:
      - "query": the input query
      - "expected": the expected structured data (e.g., supplier list)
      - "result": the actual output from the system

    This is a simplified version; in production, you would compute:
      - JSON validity
      - field precision/recall
      - evidence accuracy
      - hallucination rate
      - ranking quality
    """
    if not results:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0}

    total = len(results)
    correct = 0
    for case in results:
        expected = case.get("expected", {})
        actual = case.get("result", {})
        # Simple heuristic: if at least one supplier name matches
        exp_suppliers = expected.get("suppliers", [])
        act_suppliers = actual.get("suppliers", [])
        exp_names = {s.get("name") for s in exp_suppliers if s.get("name")}
        act_names = {s.get("name") for s in act_suppliers if s.get("name")}
        if exp_names.intersection(act_names):
            correct += 1
        # Also check if evidence is present
        # For MVP, we'll just compute a basic score

    accuracy = correct / total if total > 0 else 0.0

    # Additional metrics (stubs)
    # In a real system, compute precision/recall per field
    precision = 0.8  # placeholder
    recall = 0.75    # placeholder

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "total_cases": total,
        "correct_predictions": correct,
    }