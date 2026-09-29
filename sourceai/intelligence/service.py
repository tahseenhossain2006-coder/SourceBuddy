# sourceai/intelligence/service.py

import logging
from typing import Optional

from sourceai.intelligence.models import (
    IntelligenceRequest,
    IntelligenceResponse,
    ConfidenceAnalysis,
    MissingDataAnalysis,
    SupplierComparison,
)

from sourceai.intelligence.evidence.verifier import EvidenceVerifier
from sourceai.intelligence.confidence.analyzer import ConfidenceAnalyzer
from sourceai.intelligence.missing_data.reasoner import MissingDataReasoner
from sourceai.intelligence.filtering.parser import FilterParser
from sourceai.intelligence.filtering.evaluator import FilterEvaluator
from sourceai.intelligence.comparison.comparator import SupplierComparator

from sourceai.llm.config import LLMConfig
from sourceai.llm.provider_factory import get_all_providers
from sourceai.llm.router import ModelRouter


logger = logging.getLogger(__name__)


class IntelligenceService:
    """
    Main orchestration service for SourceAI intelligence operations.

    Architecture:

        IntelligenceService
                |
                v
           ModelRouter
                |
        +-------+-------+
        |       |       |
       Groq  OpenRouter OmniRoute
        |
        +----------------------+
        |                      |
    GPT-OSS 120B          GPT-OSS 20B
        |
        v
    automatic fallback
    """

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        router: Optional[ModelRouter] = None,
    ):
        """
        Initialize the intelligence service.

        If a ModelRouter is supplied, use it directly.

        Otherwise:
            1. Load LLM configuration.
            2. Create all configured providers.
            3. Create the canonical ModelRouter.
            4. Inject the same router into all intelligence modules.
        """

        if router is not None:
            self.router = router
            self.config = None
            self.providers = None

        else:
            self.config = config or LLMConfig.from_env()

            self.providers = get_all_providers(self.config)

            if not self.providers:
                raise RuntimeError(
                    "No LLM providers are available. "
                    "Check SourceAI LLM configuration and API keys."
                )

            self.router = ModelRouter(
                self.config,
                self.providers,
            )

        self.verifier = EvidenceVerifier(self.router)
        self.analyzer = ConfidenceAnalyzer(self.router)
        self.reasoner = MissingDataReasoner(self.router)
        self.filter_parser = FilterParser(self.router)
        self.comparator = SupplierComparator(self.router)

    def process(
        self,
        request: IntelligenceRequest,
    ) -> IntelligenceResponse:
        """
        Run the configured intelligence pipeline.

        Pipeline:
            1. Evidence verification
            2. Confidence analysis
            3. Missing-data reasoning
            4. Natural-language filtering
            5. Supplier comparison
        """

        suppliers = request.supplier_records

        if not suppliers:
            return IntelligenceResponse(
                verified_suppliers=[],
                evidence_results=None,
                confidence_results=None,
                missing_data_results=None,
                filtered_suppliers=[],
                comparison=None,
            )

        # ==============================================================
        # 1. Evidence Verification
        # ==============================================================

        evidence_results = None

        if request.enable_evidence_verification:
            evidence_results = []
            verified_suppliers = []

            for supplier in suppliers:
                source_content = (
                    supplier.get("raw_html", "")
                    or supplier.get("html", "")
                )

                source_url = (
                    supplier.get("source_url", "")
                    or supplier.get("url", "")
                )

                if not source_content:
                    verified_suppliers.append(supplier)
                    continue

                try:
                    result = self.verifier.verify(
                        supplier,
                        source_content,
                        source_url,
                    )

                    evidence_results.append(result)

                    if hasattr(result, "model_dump"):
                        supplier["verification"] = result.model_dump()
                    else:
                        supplier["verification"] = result

                    verified_suppliers.append(supplier)

                except Exception:
                    logger.exception(
                        "Evidence verification failed for supplier %s",
                        supplier.get("id"),
                    )

                    supplier["verification"] = {
                        "error": "Evidence verification failed."
                    }

                    verified_suppliers.append(supplier)

            suppliers = verified_suppliers

        # ==============================================================
        # 2. Confidence Analysis
        # ==============================================================

        confidence_results = None

        if request.enable_confidence_analysis:
            confidence_results = []

            for supplier in suppliers:
                try:
                    ranking = supplier.get("ranking") or {}

                    ranking_score = ranking.get("score", 0) or 0

                    deterministic_score = (
                        float(ranking_score) / 100.0
                    )

                    if deterministic_score <= 0:
                        fields = [
                            "moq",
                            "price_min",
                            "price_currency",
                            "certifications",
                            "contact_email",
                        ]

                        filled = sum(
                            1
                            for field in fields
                            if supplier.get(field) is not None
                        )

                        deterministic_score = (
                            filled / len(fields)
                            if fields
                            else 0.5
                        )

                    deterministic_score = max(
                        0.0,
                        min(1.0, deterministic_score),
                    )

                    source_quality = self._source_quality(
                        supplier.get("website", "")
                        or supplier.get("source_url", "")
                        or supplier.get("url", "")
                    )

                    evidence_for_supplier = None

                    if evidence_results:
                        supplier_id = supplier.get("id")

                        for evidence in evidence_results:
                            evidence_supplier_id = getattr(
                                evidence,
                                "supplier_id",
                                None,
                            )

                            if (
                                evidence_supplier_id is not None
                                and evidence_supplier_id == supplier_id
                            ):
                                evidence_for_supplier = evidence
                                break

                    analysis = self.analyzer.analyze(
                        supplier,
                        evidence_for_supplier,
                        source_quality,
                        deterministic_score,
                    )

                    confidence_results.append(analysis)

                    if hasattr(analysis, "model_dump"):
                        supplier["confidence"] = (
                            analysis.model_dump()
                        )
                    else:
                        supplier["confidence"] = analysis

                except Exception:
                    logger.exception(
                        "Confidence analysis failed for supplier %s",
                        supplier.get("id"),
                    )

                    fallback = ConfidenceAnalysis(
                        score=0.5,
                        level="medium",
                        reasoning="Confidence analysis unavailable.",
                        supporting_factors=[],
                        risk_factors=["LLM analysis failed"],
                    )

                    confidence_results.append(fallback)

                    supplier["confidence"] = (
                        fallback.model_dump()
                    )

        # ==============================================================
        # 3. Missing Data Reasoning
        # ==============================================================

        missing_data_results = None

        if request.enable_missing_data_reasoning:
            missing_data_results = []

            for supplier in suppliers:
                try:
                    source_content = (
                        supplier.get("raw_html", "")
                        or supplier.get("html", "")
                    )

                    analysis = self.reasoner.reason(
                        supplier,
                        source_content,
                    )

                    missing_data_results.append(analysis)

                    if hasattr(analysis, "model_dump"):
                        supplier["missing_data_analysis"] = (
                            analysis.model_dump()
                        )
                    else:
                        supplier["missing_data_analysis"] = analysis

                except Exception:
                    logger.exception(
                        "Missing data reasoning failed for supplier %s",
                        supplier.get("id"),
                    )

                    fallback = MissingDataAnalysis(
                        missing_fields=[]
                    )

                    missing_data_results.append(fallback)

                    supplier["missing_data_analysis"] = (
                        fallback.model_dump()
                    )

        # ==============================================================
        # 4. Natural Language Filtering
        # ==============================================================

        filtered_suppliers = suppliers

        if (
            request.enable_nl_filtering
            and request.filters
        ):
            try:
                filter_text = " ".join(
                    str(item)
                    for item in request.filters
                )

                expression = self.filter_parser.parse(
                    filter_text
                )

                if expression.conditions:
                    filtered_suppliers = [
                        supplier
                        for supplier in suppliers
                        if FilterEvaluator.evaluate(
                            supplier,
                            expression,
                        )
                    ]
                else:
                    filtered_suppliers = suppliers

            except Exception:
                logger.exception(
                    "Natural-language filtering failed."
                )

                filtered_suppliers = suppliers

        # ==============================================================
        # 5. Supplier Comparison
        # ==============================================================

        comparison = None

        if (
            request.enable_comparison
            and len(suppliers) >= 2
        ):
            try:

                def sort_key(supplier):
                    ranking = supplier.get("ranking") or {}
                    confidence = supplier.get("confidence") or {}

                    ranking_score = (
                        ranking.get("score", 0) or 0
                    )

                    confidence_score = (
                        confidence.get("score", 0) or 0
                    )

                    return (
                        ranking_score
                        if ranking_score
                        else confidence_score
                    )

                sorted_suppliers = sorted(
                    suppliers,
                    key=sort_key,
                    reverse=True,
                )

                comparison_limit = max(
                    2,
                    request.comparison_limit,
                )

                top_suppliers = sorted_suppliers[
                    :comparison_limit
                ]

                comparison = self.comparator.compare(
                    top_suppliers,
                    comparison_limit,
                )

            except Exception:
                logger.exception(
                    "Supplier comparison failed."
                )

                comparison = SupplierComparison(
                    supplier_ids=[
                        supplier.get("id", "")
                        for supplier in suppliers[
                            :request.comparison_limit
                        ]
                    ],
                    fields=[],
                    winner_by_field={},
                    overall_recommendation=None,
                    tradeoffs=[],
                    reasoning=(
                        "Comparison unavailable due to an error."
                    ),
                )

        # ==============================================================
        # Final Response
        # ==============================================================

        return IntelligenceResponse(
            verified_suppliers=suppliers,
            evidence_results=evidence_results,
            confidence_results=confidence_results,
            missing_data_results=missing_data_results,
            filtered_suppliers=filtered_suppliers,
            comparison=comparison,
        )

    @staticmethod
    def _source_quality(url: str) -> float:
        """
        Return a deterministic source-quality score.
        """

        if not url:
            return 0.5

        domain = url.lower()

        if "globalsources.com" in domain:
            return 0.75

        if "indiamart.com" in domain:
            return 0.70

        if "tradeindia.com" in domain:
            return 0.70

        if "alibaba.com" in domain:
            return 0.60

        if "amazon." in domain:
            return 0.40

        if "ebay." in domain:
            return 0.40

        if "walmart." in domain:
            return 0.40

        if any(
            tld in domain
            for tld in (
                ".com",
                ".org",
                ".net",
                ".co",
                ".in",
            )
        ):
            return 0.90

        return 0.50