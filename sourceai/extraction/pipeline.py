# sourceai/extraction/pipeline.py
import logging
from typing import List, Dict, Any, Union

from sourceai.config.settings import settings
from sourceai.extraction.scrapegraph import ScrapeGraphExtractor
from sourceai.extraction.extractors import (
    TrafilaturaExtractor,
    BeautifulSoupExtractor,
    ReadabilityExtractor,
)

logger = logging.getLogger(__name__)


def _to_dict(item: Union[dict, Any]) -> Dict[str, Any]:
    """
    Normalize a crawled item to a dict.
    Accepts either a plain dict OR a CrawlResult-style dataclass with
    attributes: url, html, status.
    """
    if isinstance(item, dict):
        return item
    return {
        "url": getattr(item, "url", None),
        "html": getattr(item, "html", None),
        "status": getattr(item, "status", None),
    }


class ExtractionPipeline:
    """
    ScrapeGraphAI primary (LLM-based), with Trafilatura → BS4 → Readability
    fallbacks.

    ScrapeGraphAI calls an LLM. When AI_ENABLED=false, it must not be
    instantiated or invoked — the pipeline runs the deterministic extractors
    only.
    """

    def __init__(self):
        # ScrapeGraphAI requires an LLM. When AI is disabled, do not even
        # construct the adapter, so no Groq/OpenRouter client is created and
        # no accidental network call can happen.
        if settings.AI_ENABLED and settings.SCRAPEGRAPH_ENABLED:
            self.scrapegraph: ScrapeGraphExtractor | None = ScrapeGraphExtractor()
        else:
            self.scrapegraph = None
            logger.info(
                "ScrapeGraphAI disabled (AI_ENABLED=%s, SCRAPEGRAPH_ENABLED=%s); "
                "using deterministic extractors only",
                settings.AI_ENABLED, settings.SCRAPEGRAPH_ENABLED,
            )

        self.fallbacks = [
            TrafilaturaExtractor(),
            BeautifulSoupExtractor(),
            ReadabilityExtractor(),
        ]

    def extract(self, crawled: List[Any]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for raw in crawled:
            item = _to_dict(raw)
            url = item.get("url")
            html = item.get("html")
            if not html:
                continue
            result = self._extract_one(url, html)
            if result:
                out.append(result)
        return out

    def _extract_one(self, url: str, html: str) -> Dict[str, Any]:
        # 1. ScrapeGraphAI (primary — only when AI is enabled)
        if self.scrapegraph is not None:
            try:
                sg = self.scrapegraph.extract(html, url)
                if sg and self._sufficient(sg):
                    sg["extraction_engine"] = "scrapegraphai"
                    return sg
            except Exception as e:
                logger.warning(f"ScrapeGraphAI failed for {url}: {e}")

        # 2. Deterministic fallbacks (always available)
        for extractor in self.fallbacks:
            try:
                result = extractor.extract(html, url)
                if result and self._sufficient(result):
                    result["extraction_engine"] = extractor.name
                    return result
            except Exception as e:
                logger.warning(f"{extractor.name} failed for {url}: {e}")

        # 3. Nothing worked — return an empty text record so pipeline continues
        logger.warning(f"All extractors failed for {url}")
        return {"url": url, "text": "", "extraction_engine": "none"}

    @staticmethod
    def _sufficient(result: Dict[str, Any]) -> bool:
        text = result.get("text") or ""
        return len(text) > 200 or bool(result.get("company_name"))