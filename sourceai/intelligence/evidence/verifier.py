# sourceai/intelligence/evidence/verifier.py

import json
import logging
from typing import List, Dict, Any

from sourceai.intelligence.models import (
    EvidenceVerificationResult,
    EvidenceItem,
    VerificationStatus,
)
from sourceai.intelligence.prompts.evidence import (
    EVIDENCE_VERIFICATION_PROMPT,
)
from sourceai.llm.router import ModelRouter
from sourceai.llm.tasks import LLMTask


logger = logging.getLogger(__name__)


class EvidenceVerifier:
    def __init__(self, router: ModelRouter):
        self.router = router

    def verify(
        self,
        supplier_data: Dict[str, Any],
        source_content: str,
        source_url: str,
    ) -> EvidenceVerificationResult:

        fields_to_verify = [
            "name",
            "country",
            "region",
            "city",
            "moq",
            "price_min",
            "price_currency",
            "certifications",
            "contact_email",
            "customization_available",
            "supplier_type",
        ]

        items: List[EvidenceItem] = []

        for field in fields_to_verify:
            value = supplier_data.get(field)

            if value is None or value == "":
                continue

            prompt = EVIDENCE_VERIFICATION_PROMPT.format(
                field=field,
                value=json.dumps(value),
                source_content=source_content[:8000],
            )

            try:
                # Canonical SourceAI LLM Router interface.
                #
                # The router automatically handles:
                #   Groq GPT-OSS 120B
                #       ↓
                #   Groq GPT-OSS 20B
                #       ↓
                #   OpenRouter
                #       ↓
                #   OmniRoute
                #
                # The same task/context is passed through the fallback chain.
                response = self.router.route(
                    LLMTask.EVIDENCE_VERIFICATION,
                    [
                        {
                            "role": "system",
                            "content": (
                                "You are a supplier evidence verification "
                                "system. Verify whether the supplied field "
                                "value is supported by the provided source. "
                                "Return only valid JSON."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                )

                result = json.loads(response)

                status_str = result.get(
                    "status",
                    "insufficient_evidence",
                )

                try:
                    status = VerificationStatus(status_str)
                except ValueError:
                    status = (
                        VerificationStatus.INSUFFICIENT_EVIDENCE
                    )

                supporting_text = result.get(
                    "supporting_text"
                )

                explanation = result.get(
                    "explanation",
                    "",
                )

                try:
                    confidence = float(
                        result.get(
                            "confidence",
                            0.5,
                        )
                    )
                except (TypeError, ValueError):
                    confidence = 0.5

                confidence = min(
                    1.0,
                    max(0.0, confidence),
                )

                # ------------------------------------------------------
                # Deterministic guard
                # ------------------------------------------------------
                #
                # Never trust an LLM-generated citation blindly.
                # supporting_text must actually exist in the source.
                #
                if supporting_text:
                    norm_support = " ".join(
                        str(supporting_text).split()
                    ).lower()

                    norm_source = " ".join(
                        source_content.split()
                    ).lower()

                    if norm_support not in norm_source:
                        supporting_text = None

                        if (
                            status
                            == VerificationStatus.VERIFIED
                        ):
                            status = (
                                VerificationStatus.PARTIALLY_SUPPORTED
                            )

                else:
                    # If the LLM did not provide supporting text,
                    # perform a deterministic direct-value check.
                    str_value = str(value).lower()

                    if str_value in source_content.lower():
                        status = (
                            VerificationStatus.VERIFIED
                        )
                        supporting_text = source_content[:200]
                    else:
                        status = (
                            VerificationStatus.INSUFFICIENT_EVIDENCE
                        )

                items.append(
                    EvidenceItem(
                        field=field,
                        value=value,
                        source_url=source_url,
                        supporting_text=supporting_text,
                        status=status,
                        explanation=explanation,
                        confidence=confidence,
                    )
                )

            except Exception as e:
                logger.warning(
                    "Evidence verification failed for field %s: %s",
                    field,
                    e,
                )

                # ------------------------------------------------------
                # Deterministic fallback
                # ------------------------------------------------------

                str_value = str(value).lower()

                if str_value in source_content.lower():
                    status = VerificationStatus.VERIFIED
                    supporting_text = source_content[:200]
                    confidence = 0.8
                    explanation = (
                        "Fallback: value present in source."
                    )
                else:
                    status = (
                        VerificationStatus.INSUFFICIENT_EVIDENCE
                    )
                    supporting_text = None
                    confidence = 0.0
                    explanation = (
                        "Value not found in source."
                    )

                items.append(
                    EvidenceItem(
                        field=field,
                        value=value,
                        source_url=source_url,
                        supporting_text=supporting_text,
                        status=status,
                        explanation=explanation,
                        confidence=confidence,
                    )
                )

        # ==============================================================
        # No verifiable fields
        # ==============================================================

        if not items:
            return EvidenceVerificationResult(
                items=[],
                overall_status=(
                    VerificationStatus.INSUFFICIENT_EVIDENCE
                ),
                overall_confidence=0.0,
            )

        # ==============================================================
        # Calculate overall verification status
        # ==============================================================

        verified_count = sum(
            1
            for item in items
            if item.status == VerificationStatus.VERIFIED
        )

        contradicted_count = sum(
            1
            for item in items
            if item.status == VerificationStatus.CONTRADICTED
        )

        if verified_count == len(items):
            overall_status = VerificationStatus.VERIFIED

        elif verified_count > 0:
            overall_status = (
                VerificationStatus.PARTIALLY_SUPPORTED
            )

        elif contradicted_count > 0:
            overall_status = (
                VerificationStatus.CONTRADICTED
            )

        else:
            overall_status = (
                VerificationStatus.INSUFFICIENT_EVIDENCE
            )

        overall_confidence = (
            sum(
                item.confidence
                for item in items
            )
            / len(items)
        )

        return EvidenceVerificationResult(
            items=items,
            overall_status=overall_status,
            overall_confidence=overall_confidence,
        )