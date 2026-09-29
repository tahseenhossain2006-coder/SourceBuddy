import json
import logging
from typing import Any, Dict, Optional

from sourceai.intelligence.models import (
    ConfidenceAnalysis,
    ConfidenceLevel,
)
from sourceai.intelligence.prompts.confidence import (
    CONFIDENCE_PROMPT,
)
from sourceai.llm.router import ModelRouter
from sourceai.llm.tasks import LLMTask

logger = logging.getLogger(__name__)


class ConfidenceAnalyzer:
    """
    Analyze confidence in extracted supplier data using the central
    SourceAI ModelRouter.
    """

    def __init__(self, router: ModelRouter):
        self.router = router

    def analyze(
        self,
        supplier: Dict[str, Any],
        evidence: Optional[Any] = None,
        source_quality: float = 0.0,
        deterministic_score: float = 0.0,
    ) -> ConfidenceAnalysis:
        context = {
            "supplier": supplier,
            "evidence": self._serialize(evidence),
            "source_quality": source_quality,
            "deterministic_score": deterministic_score,
        }

        prompt = CONFIDENCE_PROMPT.format(
            context=json.dumps(
                context,
                ensure_ascii=False,
                default=str,
                indent=2,
            )
        )

        try:
            response = self.router.route(
                LLMTask.CONFIDENCE_ANALYSIS,
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a supplier confidence-analysis "
                            "system. Analyze only the supplied data. "
                            "Do not invent evidence. Return only valid JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            return self._parse_response(
                response,
                deterministic_score,
            )

        except Exception as exc:
            logger.exception(
                "Confidence analysis failed: %s",
                exc,
            )

            return self._fallback(
                deterministic_score,
            )

    def _parse_response(
        self,
        response: str,
        deterministic_score: float,
    ) -> ConfidenceAnalysis:
        data = self._extract_json(response)

        score = data.get(
            "score",
            deterministic_score,
        )

        try:
            score = float(score)
        except (TypeError, ValueError):
            score = deterministic_score

        score = max(
            0.0,
            min(1.0, score),
        )

        raw_level = str(
            data.get(
                "level",
                self._level_for_score(score),
            )
        ).lower().strip()

        try:
            level = ConfidenceLevel(
                raw_level
            )
        except ValueError:
            level = self._level_for_score(score)

        supporting = data.get(
            "supporting_factors",
            [],
        )

        if isinstance(supporting, str):
            supporting = [supporting]

        if not isinstance(supporting, list):
            supporting = []

        risks = data.get(
            "risk_factors",
            [],
        )

        if isinstance(risks, str):
            risks = [risks]

        if not isinstance(risks, list):
            risks = []

        reasoning = str(
            data.get(
                "reasoning",
                "Confidence analysis completed.",
            )
        ).strip()

        return ConfidenceAnalysis(
            score=score,
            level=level,
            reasoning=reasoning,
            supporting_factors=[
                str(x) for x in supporting
            ],
            risk_factors=[
                str(x) for x in risks
            ],
        )

    def _extract_json(
        self,
        response: str,
    ) -> Dict[str, Any]:
        if not response:
            raise ValueError(
                "Empty confidence-analysis response."
            )

        text = response.strip()

        try:
            value = json.loads(text)

            if isinstance(value, dict):
                return value

        except json.JSONDecodeError:
            pass

        if text.startswith("```"):
            lines = text.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            try:
                value = json.loads(
                    "\n".join(lines).strip()
                )

                if isinstance(value, dict):
                    return value

            except json.JSONDecodeError:
                pass

        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end > start:
            try:
                value = json.loads(
                    text[start:end + 1]
                )

                if isinstance(value, dict):
                    return value

            except json.JSONDecodeError:
                pass

        raise ValueError(
            "Confidence response did not contain valid JSON."
        )

    def _fallback(
        self,
        deterministic_score: float,
    ) -> ConfidenceAnalysis:
        score = max(
            0.0,
            min(
                1.0,
                float(deterministic_score or 0.0),
            ),
        )

        return ConfidenceAnalysis(
            score=score,
            level=self._level_for_score(score),
            reasoning=(
                "LLM confidence analysis was unavailable; "
                "deterministic confidence score used."
            ),
            supporting_factors=[],
            risk_factors=[
                "LLM analysis unavailable"
            ],
        )

    @staticmethod
    def _level_for_score(
        score: float,
    ) -> ConfidenceLevel:
        if score >= 0.9:
            return ConfidenceLevel.VERY_HIGH

        if score >= 0.75:
            return ConfidenceLevel.HIGH

        if score >= 0.5:
            return ConfidenceLevel.MEDIUM

        if score >= 0.25:
            return ConfidenceLevel.LOW

        return ConfidenceLevel.VERY_LOW

    @staticmethod
    def _serialize(
        value: Any,
    ) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump()

        if hasattr(value, "dict"):
            return value.dict()

        return value
