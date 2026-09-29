# sourceai/intelligence/comparison/comparator.py

import json
import logging
from typing import Any, Dict, List

from sourceai.intelligence.models import (
    ComparisonField,
    SupplierComparison,
)
from sourceai.intelligence.prompts.comparison import (
    COMPARISON_PROMPT,
)
from sourceai.llm.router import ModelRouter
from sourceai.llm.tasks import LLMTask

logger = logging.getLogger(__name__)


class SupplierComparator:
    """
    Generate a structured side-by-side supplier comparison.

    All LLM inference is routed through the central SourceAI
    ModelRouter so model/provider fallback remains centralized.
    """

    def __init__(self, router: ModelRouter):
        self.router = router

    def compare(
        self,
        suppliers: List[Dict[str, Any]],
        comparison_limit: int | None = None,
    ) -> SupplierComparison:
        """
        Compare the supplied supplier records.

        The original supplier records are passed to the model as context.
        Unknown values remain unknown rather than being converted to zero.
        """

        if comparison_limit is not None:
            try:
                limit = max(2, int(comparison_limit))
                suppliers = suppliers[:limit]
            except (TypeError, ValueError):
                pass

        if not suppliers:
            return SupplierComparison(
                supplier_ids=[],
                fields=[],
                winner_by_field={},
                overall_recommendation=None,
                tradeoffs=[],
                reasoning="No suppliers were provided for comparison.",
            )

        context = self._serialize_context(
            suppliers
        )

        prompt = COMPARISON_PROMPT.format(
            context=context
        )

        try:
            response = self.router.route(
                LLMTask.SUPPLIER_COMPARISON,
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a supplier comparison system. "
                            "Compare suppliers using only the supplied "
                            "data. Do not invent missing values. "
                            "Treat unknown values as unknown rather "
                            "than zero. Return only valid JSON."
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
                suppliers,
            )

        except Exception as exc:
            logger.exception(
                "Supplier comparison failed: %s",
                exc,
            )

            return self._deterministic_fallback(
                suppliers
            )

    def _serialize_context(
        self,
        suppliers: List[Dict[str, Any]],
    ) -> str:
        """Serialize supplier records for the comparison prompt."""

        try:
            return json.dumps(
                suppliers,
                ensure_ascii=False,
                default=str,
                indent=2,
            )
        except Exception:
            return str(suppliers)

    def _parse_response(
        self,
        response: str,
        suppliers: List[Dict[str, Any]],
    ) -> SupplierComparison:
        """Parse and validate the model comparison response."""

        data = self._extract_json(
            response
        )

        supplier_ids = [
            str(
                supplier.get(
                    "supplier_id",
                    supplier.get(
                        "id",
                        supplier.get(
                            "name",
                            index,
                        ),
                    ),
                )
            )
            for index, supplier in enumerate(suppliers)
        ]

        raw_fields = data.get(
            "fields",
            [],
        )

        if not isinstance(raw_fields, list):
            raw_fields = []

        fields: List[ComparisonField] = []

        for raw_field in raw_fields:
            if not isinstance(raw_field, dict):
                continue

            field_name = str(
                raw_field.get(
                    "field",
                    "",
                )
            ).strip()

            if not field_name:
                continue

            raw_values = raw_field.get(
                "values",
                {},
            )

            if not isinstance(raw_values, dict):
                raw_values = {}

            values = {
                str(key): value
                for key, value in raw_values.items()
            }

            winner_id = raw_field.get(
                "winner_id"
            )

            if winner_id is not None:
                winner_id = str(
                    winner_id
                )

                if winner_id not in supplier_ids:
                    winner_id = None

            unit = raw_field.get(
                "unit"
            )

            if unit is not None:
                unit = str(
                    unit
                ).strip() or None

            explanation = raw_field.get(
                "explanation"
            )

            if explanation is not None:
                explanation = str(
                    explanation
                ).strip() or None

            fields.append(
                ComparisonField(
                    field=field_name,
                    values=values,
                    unit=unit,
                    winner_id=winner_id,
                    explanation=explanation,
                )
            )

        raw_winners = data.get(
            "winner_by_field",
            {},
        )

        if not isinstance(raw_winners, dict):
            raw_winners = {}

        winner_by_field = {}

        for field, supplier_id in raw_winners.items():
            field_name = str(
                field
            ).strip()

            if not field_name:
                continue

            supplier_id = str(
                supplier_id
            )

            if supplier_id in supplier_ids:
                winner_by_field[field_name] = supplier_id

        # Keep winner_by_field synchronized with valid field-level winners.
        for field in fields:
            if (
                field.winner_id is not None
                and field.field not in winner_by_field
            ):
                winner_by_field[
                    field.field
                ] = field.winner_id

        overall_recommendation = data.get(
            "overall_recommendation"
        )

        if overall_recommendation is not None:
            overall_recommendation = str(
                overall_recommendation
            ).strip() or None

            # Do not allow an arbitrary model-generated supplier ID
            # that does not exist in the compared set.
            if (
                overall_recommendation not in supplier_ids
            ):
                overall_recommendation = None

        raw_tradeoffs = data.get(
            "tradeoffs",
            [],
        )

        if isinstance(raw_tradeoffs, str):
            raw_tradeoffs = [
                raw_tradeoffs
            ]

        if not isinstance(raw_tradeoffs, list):
            raw_tradeoffs = []

        tradeoffs = [
            str(item)
            for item in raw_tradeoffs
            if item is not None
        ]

        reasoning = str(
            data.get(
                "reasoning",
                "Comparison generated from the supplied supplier data.",
            )
        ).strip()

        return SupplierComparison(
            supplier_ids=supplier_ids,
            fields=fields,
            winner_by_field=winner_by_field,
            overall_recommendation=overall_recommendation,
            tradeoffs=tradeoffs,
            reasoning=reasoning,
        )

    def _extract_json(
        self,
        response: str,
    ) -> Dict[str, Any]:
        """Extract a JSON object from the model response."""

        if not response:
            raise ValueError(
                "Empty supplier-comparison response."
            )

        text = response.strip()

        # Normal JSON.
        try:
            value = json.loads(
                text
            )

            if isinstance(value, dict):
                return value

        except json.JSONDecodeError:
            pass

        # Markdown JSON fence.
        if text.startswith("```"):
            lines = text.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            fenced = "\n".join(
                lines
            ).strip()

            try:
                value = json.loads(
                    fenced
                )

                if isinstance(value, dict):
                    return value

            except json.JSONDecodeError:
                pass

        # JSON surrounded by accidental explanatory text.
        start = text.find(
            "{"
        )
        end = text.rfind(
            "}"
        )

        if start != -1 and end > start:
            candidate = text[
                start : end + 1
            ]

            try:
                value = json.loads(
                    candidate
                )

                if isinstance(value, dict):
                    return value

            except json.JSONDecodeError:
                pass

        raise ValueError(
            "Supplier-comparison response did not contain valid JSON."
        )

    def _deterministic_fallback(
        self,
        suppliers: List[Dict[str, Any]],
    ) -> SupplierComparison:
        """
        Conservative deterministic fallback.

        This creates a comparison from fields explicitly present in
        the supplier records. It does not treat missing values as zero.
        """

        supplier_ids = [
            str(
                supplier.get(
                    "supplier_id",
                    supplier.get(
                        "id",
                        supplier.get(
                            "name",
                            index,
                        ),
                    ),
                )
            )
            for index, supplier in enumerate(suppliers)
        ]

        if not suppliers:
            return SupplierComparison(
                supplier_ids=[],
                fields=[],
                winner_by_field={},
                overall_recommendation=None,
                tradeoffs=[],
                reasoning="No suppliers were provided for comparison.",
            )

        candidate_fields = [
            "moq",
            "price_min",
            "price_max",
            "country",
            "region",
            "city",
            "supplier_type",
            "certifications",
            "customization_available",
        ]

        fields: List[ComparisonField] = []
        winner_by_field: Dict[str, str] = {}

        for field_name in candidate_fields:
            values: Dict[str, Any] = {}

            for supplier_id, supplier in zip(
                supplier_ids,
                suppliers,
            ):
                if field_name in supplier:
                    value = supplier.get(
                        field_name
                    )

                    if value not in (
                        None,
                        "",
                    ):
                        values[
                            supplier_id
                        ] = value

            if not values:
                continue

            winner_id = self._deterministic_winner(
                field_name,
                values,
            )

            explanation = None

            if winner_id is not None:
                winner_by_field[
                    field_name
                ] = winner_id

                explanation = (
                    "Selected using the available supplier "
                    "values; missing values were not treated "
                    "as zero."
                )

            fields.append(
                ComparisonField(
                    field=field_name,
                    values=values,
                    winner_id=winner_id,
                    explanation=explanation,
                )
            )

        return SupplierComparison(
            supplier_ids=supplier_ids,
            fields=fields,
            winner_by_field=winner_by_field,
            overall_recommendation=None,
            tradeoffs=[],
            reasoning=(
                "Deterministic comparison generated because "
                "LLM comparison was unavailable. Missing "
                "values were not treated as zero."
            ),
        )

    def _deterministic_winner(
        self,
        field_name: str,
        values: Dict[str, Any],
    ) -> str | None:
        """
        Determine an objective winner only where numeric comparison
        is meaningful.

        No overall supplier recommendation is fabricated here.
        """

        numeric_lower_is_better = {
            "moq",
            "price_min",
            "price_max",
        }

        if field_name not in numeric_lower_is_better:
            return None

        numeric_values = {}

        for supplier_id, value in values.items():
            try:
                if isinstance(
                    value,
                    bool,
                ):
                    continue

                numeric_values[
                    supplier_id
                ] = float(value)

            except (
                TypeError,
                ValueError,
            ):
                continue

        if not numeric_values:
            return None

        return min(
            numeric_values,
            key=numeric_values.get,
        )
