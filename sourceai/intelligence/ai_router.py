# sourceai/intelligence/ai_router.py
"""
Legacy compatibility layer for the intelligence package.

The production LLM routing implementation lives in sourceai.llm.router.

This module intentionally contains:
- no provider-specific HTTP calls
- no model names
- no Qwen/Llama defaults
- no OmniRoute-specific routing logic

It exists temporarily so older intelligence integrations can migrate
without breaking the application.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from sourceai.llm.router import LLMTask, ModelRouter


class AITask(str, Enum):
    """
    Backward-compatible aliases for the old intelligence task names.

    New code should use LLMTask directly.
    """

    REQUIREMENT_EXTRACTION = LLMTask.REQUIREMENT_EXTRACTION.value
    QUERY_PLANNING = LLMTask.QUERY_NORMALIZATION.value
    QUERY_EXPANSION = LLMTask.QUERY_EXPANSION.value
    SUPPLIER_EXTRACTION = LLMTask.SUPPLIER_EXTRACTION.value
    SUPPLIER_RANKING = LLMTask.RANKING.value
    EVIDENCE_VERIFICATION = LLMTask.EVIDENCE_VERIFICATION.value
    CONFIDENCE_ANALYSIS = LLMTask.CONFIDENCE_ANALYSIS.value
    MISSING_DATA_REASONING = LLMTask.MISSING_DATA_REASONING.value
    NL_FILTERING = LLMTask.NL_FILTERING.value
    SUPPLIER_COMPARISON = LLMTask.COMPARISON.value
    GENERAL_REASONING = LLMTask.GENERAL_REASONING.value


class AIRouter:
    """
    Temporary compatibility wrapper around the canonical ModelRouter.

    This class does NOT implement routing itself.
    """

    def __init__(self, router: ModelRouter):
        self._router = router

    @property
    def router(self) -> ModelRouter:
        return self._router

    @staticmethod
    def _map_task(task: AITask) -> LLMTask:
        mapping = {
            AITask.REQUIREMENT_EXTRACTION: LLMTask.REQUIREMENT_EXTRACTION,
            AITask.QUERY_PLANNING: LLMTask.QUERY_NORMALIZATION,
            AITask.QUERY_EXPANSION: LLMTask.QUERY_EXPANSION,
            AITask.SUPPLIER_EXTRACTION: LLMTask.SUPPLIER_EXTRACTION,
            AITask.SUPPLIER_RANKING: LLMTask.RANKING,
            AITask.EVIDENCE_VERIFICATION: LLMTask.EVIDENCE_VERIFICATION,
            AITask.CONFIDENCE_ANALYSIS: LLMTask.CONFIDENCE_ANALYSIS,
            AITask.MISSING_DATA_REASONING: LLMTask.MISSING_DATA_REASONING,
            AITask.NL_FILTERING: LLMTask.NL_FILTERING,
            AITask.SUPPLIER_COMPARISON: LLMTask.COMPARISON,
            AITask.GENERAL_REASONING: LLMTask.GENERAL_REASONING,
        }

        try:
            return mapping[task]
        except KeyError as exc:
            raise ValueError(f"Unsupported intelligence task: {task}") from exc

    def route(
        self,
        task: AITask,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """
        Preserve the old route() contract while delegating completely
        to the canonical ModelRouter.
        """
        return self._router.route(
            self._map_task(task),
            prompt,
            **kwargs,
        )