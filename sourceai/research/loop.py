# sourceai/research/loop.py
import logging
from typing import Dict, Any, List
from datetime import datetime
from sourceai.config.settings import settings

logger = logging.getLogger(__name__)

class AutonomousResearch:
    def __init__(self, agent):
        self.agent = agent

    async def run(self, query: str) -> Dict[str, Any]:
        start = datetime.utcnow()
        plan = self.agent.planner.plan(query)
        all_suppliers: List[Dict] = []
        used_urls = set()
        iterations = 0
        stop_reason = "max_iterations"

        for iterations in range(1, settings.RESEARCH_MAX_ITERATIONS + 1):
            elapsed = (datetime.utcnow() - start).total_seconds()
            if elapsed > settings.RESEARCH_MAX_WALL_TIME:
                stop_reason = "wall_time_exceeded"; break

            results = await self.agent._execute_search(plan)
            fresh = [r for r in results if r.url not in used_urls]
            if not fresh:
                stop_reason = "no_new_information"; break
            used_urls.update(r.url for r in fresh)

            suppliers = await self.agent._extract_suppliers(fresh, plan)
            all_suppliers.extend(suppliers)

            if self._sufficient(all_suppliers, plan):
                stop_reason = "sufficient_evidence"; break

            # refine query
            plan = await self.agent._refine_plan(plan, all_suppliers)

        return {
            "query": query,
            "iterations": iterations,
            "stop_reason": stop_reason,
            "suppliers": self.agent._finalize(all_suppliers, plan, stop_reason),
            "budget": {
                "max_iterations": settings.RESEARCH_MAX_ITERATIONS,
                "elapsed_seconds": (datetime.utcnow() - start).total_seconds(),
            },
        }

    def _sufficient(self, suppliers, plan) -> bool:
        if len(suppliers) < settings.RESEARCH_MIN_SUPPLIERS:
            return False
        for s in suppliers:
            if s.get("moq") and s.get("price"):
                return True
        return False