import json
import logging
from typing import Any, Dict, List

from sourceai.intelligence.models import (
    ImportanceLevel,
    MissingDataAnalysis,
    MissingDataReason,
)
from sourceai.intelligence.prompts.missing_data import (
    MISSING_DATA_PROMPT,
)
from sourceai.llm.router import ModelRouter
from sourceai.llm.tasks import LLMTask

logger = logging.getLogger(__name__)


class MissingDataReasoner:
    """
    Identify important missing supplier information through the
    central SourceAI ModelRouter.
    """

    def __init__(self, router: ModelRouter):
        self.router = router

    def reason(
        self,
        supplier: Dict[str, Any],
        source_content: str = "",
    ) -> MissingDataAnalysis:
        context = {
            "supplier": supplier,
            "source_content": source_content or "",
        }

        context_json = json.dumps(
            context,
            ensure_ascii=False,
            default=str,
            indent=2,
        )

        # Replace only the intended context placeholder.
        # Do not use str.format() because the prompt contains
        # literal JSON braces in its examples/instructions.
        prompt = MISSING_DATA_PROMPT.replace(
            "{context}",
            context_json,
        )

        try:
            response = self.router.route(
                LLMTask.MISSING_DATA_REASONING,
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a supplier missing-data "
                            "analysis system. Identify only fields "
                            "that are genuinely missing or uncertain. "
                            "Return only valid JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            return self._parse_response(
                response
            )

        except Exception as exc:
            logger.exception(
                "Missing-data reasoning failed: %s",
                exc,
            )

            return MissingDataAnalysis(
                missing_fields=self._deterministic_missing(
                    supplier
                )
            )

    def _parse_response(
        self,
        response: str,
    ) -> MissingDataAnalysis:
        data = self._extract_json(response)

        raw_items = data.get(
            "missing_fields"
        )

        if raw_items is None:
            raw_items = data.get(
                "reasoning",
                [],
            )

        if not isinstance(raw_items, list):
            raw_items = []

        results: List[MissingDataReason] = []

        for item in raw_items:
            if not isinstance(item, dict):
                continue

            field = str(
                item.get(
                    "field",
                    "",
                )
            ).strip()

            if not field:
                continue

            reason = str(
                item.get(
                    "reason",
                    "Information is missing.",
                )
            ).strip()

            importance_raw = str(
                item.get(
                    "importance",
                    "medium",
                )
            ).lower().strip()

            try:
                importance = ImportanceLevel(
                    importance_raw
                )
            except ValueError:
                importance = ImportanceLevel.MEDIUM

            likely_source = item.get(
                "likely_source"
            )

            if likely_source is not None:
                likely_source = str(
                    likely_source
                ).strip() or None

            recommended_action = str(
                item.get(
                    "recommended_action",
                    "Verify this information with the supplier.",
                )
            ).strip()

            results.append(
                MissingDataReason(
                    field=field,
                    reason=reason,
                    importance=importance,
                    likely_source=likely_source,
                    recommended_action=recommended_action,
                )
            )

        return MissingDataAnalysis(
            missing_fields=results
        )

    def _extract_json(
        self,
        response: str,
    ) -> Dict[str, Any]:
        if not response:
            raise ValueError(
                "Empty missing-data response."
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
            "Missing-data response did not contain valid JSON."
        )

    def _deterministic_missing(
        self,
        supplier: Dict[str, Any],
    ) -> List[MissingDataReason]:
        required_fields = {
            "moq": (
                "Minimum order quantity is missing.",
                ImportanceLevel.HIGH,
                "Supplier product page or direct supplier contact",
            ),
            "price_min": (
                "Minimum price is missing.",
                ImportanceLevel.HIGH,
                "Supplier quotation or product page",
            ),
            "price_currency": (
                "Price currency is missing.",
                ImportanceLevel.MEDIUM,
                "Supplier quotation",
            ),
            "contact_email": (
                "Supplier contact email is missing.",
                ImportanceLevel.MEDIUM,
                "Supplier website or contact page",
            ),
            "certifications": (
                "Supplier certifications are missing.",
                ImportanceLevel.MEDIUM,
                "Supplier certification documents",
            ),
        }

        results = []

        for field, (
            reason,
            importance,
            likely_source,
        ) in required_fields.items():

            value = supplier.get(field)

            if value is None or value == "":
                results.append(
                    MissingDataReason(
                        field=field,
                        reason=reason,
                        importance=importance,
                        likely_source=likely_source,
                        recommended_action=(
                            f"Request or verify the supplier's {field}."
                        ),
                    )
                )

        return results
