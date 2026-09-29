# sourceai/intelligence/filtering/parser.py

import json
import logging
from typing import Any

from sourceai.intelligence.models import (
    FilterCondition,
    FilterExpression,
    FilterOperator,
)
from sourceai.intelligence.prompts.filtering import (
    FILTER_PROMPT,
)
from sourceai.llm.router import ModelRouter
from sourceai.llm.tasks import LLMTask

logger = logging.getLogger(__name__)


class FilterParser:
    """
    Convert natural-language supplier filters into structured
    FilterExpression objects.

    All LLM inference is routed through the central SourceAI
    ModelRouter so provider/model fallback remains centralized.
    """

    def __init__(self, router: ModelRouter):
        self.router = router

    def parse(
        self,
        filter_text: str,
    ) -> FilterExpression:
        """
        Parse a natural-language filter instruction.

        Example:
            "manufacturers from India under 500 MOQ"
        """

        if not filter_text or not filter_text.strip():
            return FilterExpression(
                conditions=[],
                logic="AND",
            )

        prompt = FILTER_PROMPT.format(
            filter_text=filter_text.strip()
        )

        try:
            response = self.router.route(
                LLMTask.NL_FILTERING,
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a natural-language supplier "
                            "filter parsing system. Convert the "
                            "user's filter instruction into the "
                            "requested structured JSON format. "
                            "Do not invent filter conditions. "
                            "Return only valid JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            return self._parse_response(response)

        except Exception as exc:
            logger.exception(
                "Natural-language filter parsing failed: %s",
                exc,
            )

            return FilterExpression(
                conditions=[],
                logic="AND",
            )

    def _parse_response(
        self,
        response: str,
    ) -> FilterExpression:
        """Parse and validate the LLM response."""

        data = self._extract_json(response)

        raw_conditions = data.get(
            "conditions",
            [],
        )

        if not isinstance(raw_conditions, list):
            raw_conditions = []

        conditions = []

        for raw_condition in raw_conditions:
            if not isinstance(raw_condition, dict):
                continue

            field = str(
                raw_condition.get(
                    "field",
                    "",
                )
            ).strip()

            if not field:
                continue

            operator = self._normalize_operator(
                raw_condition.get("operator")
            )

            value = raw_condition.get(
                "value",
                None,
            )

            unit = raw_condition.get(
                "unit",
                None,
            )

            if unit is not None:
                unit = str(unit).strip() or None

            conditions.append(
                FilterCondition(
                    field=field,
                    operator=operator,
                    value=value,
                    unit=unit,
                )
            )

        logic = str(
            data.get(
                "logic",
                "AND",
            )
        ).strip().upper()

        if logic not in {
            "AND",
            "OR",
            "NOT",
        }:
            logic = "AND"

        return FilterExpression(
            conditions=conditions,
            logic=logic,
        )

    def _extract_json(
        self,
        response: str,
    ) -> dict[str, Any]:
        """Extract a JSON object from the model response."""

        if not response:
            raise ValueError(
                "Empty filter-parser response."
            )

        text = response.strip()

        # Normal JSON.
        try:
            value = json.loads(text)

            if isinstance(value, dict):
                return value

        except json.JSONDecodeError:
            pass

        # Markdown JSON block.
        if text.startswith("```"):
            lines = text.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            fenced = "\n".join(lines).strip()

            try:
                value = json.loads(fenced)

                if isinstance(value, dict):
                    return value

            except json.JSONDecodeError:
                pass

        # JSON surrounded by accidental explanatory text.
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end > start:
            candidate = text[
                start : end + 1
            ]

            try:
                value = json.loads(candidate)

                if isinstance(value, dict):
                    return value

            except json.JSONDecodeError:
                pass

        raise ValueError(
            "Filter-parser response did not contain valid JSON."
        )

    def _normalize_operator(
        self,
        value: Any,
    ) -> FilterOperator:
        """Normalize an LLM operator to FilterOperator."""

        if isinstance(value, FilterOperator):
            return value

        if value is not None:
            normalized = str(
                value
            ).strip().lower()

            try:
                return FilterOperator(
                    normalized
                )

            except ValueError:
                pass

        # Safe fallback. Invalid model output must not break the
        # intelligence pipeline.
        return FilterOperator.EQ
