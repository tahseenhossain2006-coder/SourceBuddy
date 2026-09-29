# sourceai/llm/integration.py
import json
import logging
import re
from typing import List, Dict, Any, Optional

from sourceai.config.settings import settings
from sourceai.llm.deterministic import DeterministicSupplierExtractor
from sourceai.llm.router import ModelRouter
from sourceai.llm.tasks import LLMTask
from sourceai.llm.structured import (
    RequirementResult,
    SupplierExtractionResult,
    ProductExtractionResult,
    EntityResolutionResult,
    ReconciliationResult,
    ContradictionResult,
    RiskAnalysisResult,
    ComparisonResult,
)
from sourceai.llm.security import detect_prompt_injection

logger = logging.getLogger(__name__)


class LLMIntegration:
    def __init__(self, router: ModelRouter, max_retries: int = 2):
        self.router = router
        self.max_retries = max_retries

    # ------------------------------------------------------------------
    # Low-level call + parse
    # ------------------------------------------------------------------
    def _call_llm(self, task: LLMTask, prompt: str, max_tokens: int = 1024) -> str:
        last_error: Optional[BaseException] = None
        for attempt in range(self.max_retries + 1):
            try:
                return self.router.route(
                    task.value,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.1,
                )
            except Exception as e:
                last_error = e
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s",
                    attempt + 1, self.max_retries + 1, e,
                )
        raise RuntimeError(
            f"All LLM attempts failed for task {task.value}"
        ) from last_error

    def _parse_json(self, response: str, model_class):
        """
        Parse a JSON object from an LLM response.

        Handles:
          - plain JSON
          - ```json fenced blocks
          - ``` fenced blocks (no language tag)
          - a one-element list wrapping the object
        """
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"```json\s*([\s\S]*?)\s*```", response)
            if match:
                try:
                    data = json.loads(match.group(1))
                except Exception:
                    raise ValueError("Invalid JSON in response")
            else:
                match = re.search(r"```\s*([\s\S]*?)\s*```", response)
                if match:
                    try:
                        data = json.loads(match.group(1))
                    except Exception:
                        raise ValueError("Invalid JSON in response")
                else:
                    raise ValueError("Response is not valid JSON")

        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
            data = data[0]

        return model_class.model_validate(data)

    # ------------------------------------------------------------------
    # Requirement understanding
    # ------------------------------------------------------------------
    def understand_requirement(self, user_query: str) -> RequirementResult:
        if detect_prompt_injection(user_query, self.router):
            raise ValueError("Security violation detected in user query.")
        prompt = (
            "Extract structured requirements from the following user request:\n"
            f"{user_query}\n"
            "Return only valid JSON."
        )
        response = self._call_llm(LLMTask.REQUIREMENT_UNDERSTANDING, prompt)
        return self._parse_json(response, RequirementResult)

    # ------------------------------------------------------------------
    # Supplier extraction
    # ------------------------------------------------------------------
    def extract_suppliers(
        self, extracted_pages: List[Dict[str, Any]]
    ) -> List[SupplierExtractionResult]:
        """
        Extract suppliers from crawled pages.

        When AI_ENABLED=false, uses the deterministic extractor (regex +
        dictionaries + HTML heuristics). No network calls, no LLM.

        When AI_ENABLED=true, uses the LLM extractor.
        """
        if not settings.AI_ENABLED:
            logger.info(
                "AI_ENABLED=false; using deterministic supplier extraction"
            )
            return DeterministicSupplierExtractor().extract_batch(extracted_pages)

        results: List[SupplierExtractionResult] = []
        for page in extracted_pages:
            try:
                result = self._extract_single_supplier(page)
                results.append(result)
            except Exception as e:
                logger.warning(
                    "Supplier extraction failed for %s: %s",
                    page.get("url", "unknown"), e,
                )
        return results

    def _extract_single_supplier(
        self, page: Dict[str, Any]
    ) -> SupplierExtractionResult:
        html = page.get("text", "")[:8000]
        url = page.get("url", "")

        prompt = (
            "Extract supplier information from the following webpage text.\n"
            f"Source URL: {url}\n\n"
            "Return ONE JSON object (not a list, not an array). "
            "Start with { and end with }.\n"
            "Rules:\n"
            "- `products`: a list of SHORT STRINGS, e.g. "
            '["Stainless steel bottle", "Insulated flask"]. Do NOT nest objects.\n'
            "- `certifications`: a list of SHORT STRINGS, e.g. "
            '["ISO 9001", "CE"].\n'
            "- `moq`: integer if present, else null.\n"
            "- `price`: number if present, else null.\n"
            "- Missing fields must be null, not guessed.\n\n"
            "Text:\n"
            f"{html}\n"
        )

        response = self._call_llm(
            LLMTask.SUPPLIER_EXTRACTION, prompt, max_tokens=2048
        )
        result = self._parse_json(response, SupplierExtractionResult)
        result.source_urls = [url] if url else result.source_urls
        return result

    # ------------------------------------------------------------------
    # Product extraction
    # ------------------------------------------------------------------
    def extract_products(
        self, extracted_pages: List[Dict[str, Any]]
    ) -> List[ProductExtractionResult]:
        results: List[ProductExtractionResult] = []
        for page in extracted_pages:
            try:
                html = page.get("text", "")[:3000]
                url = page.get("url", "")
                prompt = (
                    "Extract product information from the following text.\n"
                    f"Source URL: {url}\n\n{html}\n\nReturn valid JSON."
                )
                response = self._call_llm(
                    LLMTask.PRODUCT_EXTRACTION, prompt, max_tokens=2048
                )
                result = self._parse_json(response, ProductExtractionResult)
                result.source_url = url
                results.append(result)
            except Exception as e:
                logger.warning(
                    "Product extraction failed for %s: %s",
                    page.get("url", "unknown"), e,
                )
        return results

    # ------------------------------------------------------------------
    # Evidence / ranking
    # ------------------------------------------------------------------
    def verify_evidence(
        self, suppliers: List[SupplierExtractionResult]
    ) -> List[SupplierExtractionResult]:
        return suppliers

    def rank_suppliers(
        self,
        suppliers: List[Any],
        constraints: Dict[str, Any],
    ) -> List[Any]:
        """
        Deterministic scoring. Accepts dicts or Pydantic models and returns
        the same objects sorted by an assigned confidence score.
        """
        def _get(obj: Any, key: str, default: Any = None) -> Any:
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        def _set(obj: Any, key: str, value: Any) -> None:
            if isinstance(obj, dict):
                obj[key] = value
            else:
                setattr(obj, key, value)

        for s in suppliers:
            score = 0
            moq = _get(s, "moq")
            price = _get(s, "price")
            country = _get(s, "country")
            supplier_type = _get(s, "supplier_type")
            website = _get(s, "website")
            email = _get(s, "email")
            products = _get(s, "products")

            if moq and constraints.get("max_moq") and moq <= constraints["max_moq"]:
                score += 20
            if price and constraints.get("max_price") and price <= constraints["max_price"]:
                score += 20
            if (
                country
                and constraints.get("target_country")
                and str(country).lower() == str(constraints["target_country"]).lower()
            ):
                score += 20
            if (
                supplier_type
                and constraints.get("supplier_type")
                and str(supplier_type).lower() == str(constraints["supplier_type"]).lower()
            ):
                score += 20
            if website or email:
                score += 10
            if products:
                score += 10

            _set(s, "confidence", score / 100.0)

        return sorted(
            suppliers,
            key=lambda x: _get(x, "confidence", 0.0),
            reverse=True,
        )

    # ------------------------------------------------------------------
    # Comparison / risk / final answer
    # ------------------------------------------------------------------
    def compare_suppliers(
        self,
        supplier_ids: List[str],
        suppliers: List[SupplierExtractionResult],
    ) -> ComparisonResult:
        fields = ["moq", "price", "country", "supplier_type", "products", "certifications"]
        field_values: Dict[str, Dict[str, Any]] = {f: {} for f in fields}
        for s in suppliers:
            for f in fields:
                field_values[f][s.supplier_name or s.company_name or "unknown"] = getattr(
                    s, f, None
                )
        winner_by_field: Dict[str, str] = {}
        for f in fields:
            if f in ["moq", "price"]:
                valid = {k: v for k, v in field_values[f].items() if v is not None}
                if valid:
                    winner_by_field[f] = min(valid, key=valid.get)
            else:
                for k, v in field_values[f].items():
                    if v is not None:
                        winner_by_field[f] = k
                        break
        return ComparisonResult(
            supplier_ids=supplier_ids,
            fields=field_values,
            winner_by_field=winner_by_field,
            overall_recommendation=supplier_ids[0] if supplier_ids else None,
            tradeoffs=[],
            reasoning="Based on objective criteria.",
        )

    def analyze_risk(self, supplier: SupplierExtractionResult) -> RiskAnalysisResult:
        risks: List[str] = []
        positives: List[str] = []
        if not supplier.website and not supplier.email:
            risks.append("Missing contact information")
        if supplier.moq is None:
            risks.append("MOQ unknown")
        if supplier.price is None:
            risks.append("Price unknown")
        if not supplier.certifications:
            risks.append("No certifications mentioned")
        if supplier.website:
            positives.append("Has website")
        if supplier.products:
            positives.append("Has product list")
        level = "low" if len(risks) <= 2 else "medium" if len(risks) <= 4 else "high"
        return RiskAnalysisResult(
            risk_level=level,
            risk_factors=risks,
            positive_signals=positives,
            recommendation=(
                "Verify contact details and request quote."
                if "Missing contact" in risks
                else "Supplier appears reasonably complete."
            ),
            evidence={},
        )

    def generate_final_answer(self, suppliers: List[Any], plan) -> str:
        if not suppliers:
            return "No suppliers found matching your criteria."

        def _get(obj: Any, key: str, default: Any = None) -> Any:
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        answer = f"I found {len(suppliers)} supplier(s):\n\n"
        for idx, s in enumerate(suppliers, 1):
            name = (
                _get(s, "supplier_name")
                or _get(s, "company_name")
                or "Unknown"
            )
            answer += f"{idx}. {name}\n"

            country = _get(s, "country")
            city = _get(s, "city")
            if country:
                answer += f"   Location: {country}"
                if city:
                    answer += f", {city}"
                answer += "\n"

            moq = _get(s, "moq")
            if moq:
                answer += f"   MOQ: {moq} pieces\n"

            price = _get(s, "price")
            if price:
                answer += f"   Price: {price} {_get(s, 'currency') or 'USD'}\n"

            mfg = _get(s, "manufacturer_status")
            if mfg:
                answer += f"   Manufacturer: {mfg}\n"

            if _get(s, "whatsapp"):
                answer += "   WhatsApp: Available\n"

            website = _get(s, "website")
            if website:
                answer += f"   Website: {website}\n"

            certs = _get(s, "certifications") or []
            if certs:
                answer += f"   Certifications: {', '.join(map(str, certs))}\n"

            products = _get(s, "products") or []
            if products:
                shown = ", ".join(map(str, products[:3]))
                tail = "..." if len(products) > 3 else ""
                answer += f"   Products: {shown}{tail}\n"

            conf = _get(s, "confidence", 0.0) or 0.0
            answer += f"   Confidence: {conf:.0%}\n\n"

        return answer