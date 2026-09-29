from typing import List, Dict, Any
from sourceai.search.agent import SearchAgent
from sourceai.evaluation.metrics import compute_metrics

class EvaluationRunner:
    def __init__(self, agent: SearchAgent):
        self.agent = agent

    async def run(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for case in dataset:
            query = case["query"]
            expected = case["expected"]
            result = await self.agent.search(query)
            results.append({"query": query, "result": result, "expected": expected})
        return compute_metrics(results)