# sourceai/search/agent.py
import asyncio
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from sourceai.config.settings import settings
from sourceai.search.planner import SearchPlanner, SearchPlan
from sourceai.search.router import SearchRouter
from sourceai.crawling.manager import CrawlManager
from sourceai.extraction.pipeline import ExtractionPipeline
from sourceai.llm.integration import LLMIntegration
from sourceai.interfaces import factory as iface_factory
from sourceai.llm.router import ModelRouter
from sourceai.llm.tasks import LLMTask
from sourceai.storage.postgres import PostgresStorage
from sourceai.storage.opensearch import OpenSearchIndexer
from sourceai.storage.redis import RedisCache
from sourceai.security.url_validator import is_safe_url

logger = logging.getLogger(__name__)


class SearchAgent:
    def __init__(self, llm_router: ModelRouter):
        self.planner = SearchPlanner()
        self.router = SearchRouter()
        self.crawler = CrawlManager()
        self.extractor = ExtractionPipeline()
        self.llm = LLMIntegration(llm_router)
        self.db = PostgresStorage()
        self.indexer = OpenSearchIndexer()
        self.cache = RedisCache()
        self.request_id: Optional[str] = None
        self.research_stopped_reason: Optional[str] = None

        # Interface-based components — implementation chosen by the factory
        # based on AI_ENABLED. When AI_ENABLED=false, every component here
        # is deterministic and does not make network calls.
        self.extractor_iface = iface_factory.get_semantic_extractor()
        self.ranker_iface = iface_factory.get_semantic_ranker()
        self.answer_iface = iface_factory.get_answer_generator()

    # ------------------------------------------------------------------
    # Public entry point: standard single-pass search
    # ------------------------------------------------------------------
    async def search(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Single-pass search with persistence."""
        self.request_id = str(uuid.uuid4())
        logger.info(
            "Search started (single pass): %s - Query: %s - User: %s",
            self.request_id, query[:100], user_id,
        )

        plan = self.planner.plan(query)
        all_results = await self._execute_search(plan)
        suppliers = await self._extract_suppliers(all_results, plan)
        ranked = self._finalize(suppliers, plan, stop_reason="single_pass")

        db_search_id = await self._persist_search(query, plan, ranked, user_id)
        return self._build_response(ranked, plan, "single_pass", db_search_id=db_search_id)

    # ------------------------------------------------------------------
    # Autonomous research loop
    # ------------------------------------------------------------------
    async def research(
        self,
        query: str,
        user_id: Optional[str] = None,
        max_iterations: int = 3,
    ) -> Dict[str, Any]:
        """Autonomous research loop with iterative refinement and budget control."""
        self.request_id = str(uuid.uuid4())
        self.research_stopped_reason = None
        logger.info(
            "Autonomous research started: %s - Query: %s - User: %s",
            self.request_id, query[:100], user_id,
        )

        max_searches = 3
        max_urls = 20
        max_crawl_pages = 10
        max_llm_calls = 5
        max_wall_time_seconds = 120
        start_time = datetime.utcnow()

        plan = self.planner.plan(query)
        all_suppliers: List[Any] = []
        all_results: List = []
        iteration = 0
        used_searches = 0

        while iteration < max_iterations:
            iteration += 1
            logger.info("Research iteration %s/%s", iteration, max_iterations)

            results = await self._execute_search(plan, limit=10)
            all_results.extend(results)
            used_searches += len(plan.expanded_queries)
            if len(all_results) > max_urls:
                all_results = all_results[:max_urls]

            suppliers = await self._extract_suppliers(results, plan)
            all_suppliers.extend(suppliers)

            if self._enough_evidence(all_suppliers, plan):
                self.research_stopped_reason = "sufficient_evidence"
                logger.info("Sufficient evidence found; stopping research.")
                break

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > max_wall_time_seconds:
                self.research_stopped_reason = "budget_exhausted (time)"
                logger.warning("Wall-time budget exhausted.")
                break
            if used_searches >= max_searches:
                self.research_stopped_reason = "budget_exhausted (searches)"
                logger.warning("Search budget exhausted.")
                break
            if len(all_suppliers) > max_crawl_pages * 2:
                self.research_stopped_reason = "budget_exhausted (suppliers)"
                break

            plan = await self._refine_plan(plan, all_suppliers)
            if not plan.expanded_queries:
                self.research_stopped_reason = "no_new_queries"
                break
        else:
            self.research_stopped_reason = "max_iterations_reached"

        ranked = self._finalize(
            all_suppliers, plan, stop_reason=self.research_stopped_reason
        )
        db_search_id = await self._persist_search(query, plan, ranked, user_id)
        return self._build_response(
            ranked, plan, self.research_stopped_reason or "completed",
            db_search_id=db_search_id,
        )

    # ------------------------------------------------------------------
    # Persistence helper
    # ------------------------------------------------------------------
    async def _persist_search(
        self,
        query: str,
        plan: SearchPlan,
        suppliers: List[Dict],
        user_id: Optional[str],
    ) -> Optional[str]:
        if not user_id:
            logger.warning("No user_id provided; skipping DB persistence")
            return None

        try:
            await self.db.connect()
            async with self.db.pool.acquire() as conn:
                plan_dict = (
                    plan.model_dump() if hasattr(plan, "model_dump") else plan
                )
                plan_json = json.dumps(plan_dict, default=str)

                search_id = await conn.fetchval(
                    """
                    INSERT INTO searches (user_id, query, search_plan, status,
                                          created_at, updated_at)
                    VALUES ($1, $2, $3, 'completed', NOW(), NOW())
                    RETURNING id
                    """,
                    user_id,
                    query,
                    plan_json,
                )

                inserted = 0
                skipped = 0
                for s in suppliers:
                    if hasattr(s, "model_dump"):
                        s = s.model_dump()
                    if not isinstance(s, dict):
                        continue

                    name = s.get("supplier_name") or s.get("company_name")

                    source_url = None
                    srcs = s.get("source_urls") or []
                    if isinstance(srcs, list) and srcs:
                        source_url = srcs[0]
                    elif s.get("website"):
                        source_url = s["website"]

                    has_identity = (
                        bool(name)
                        or bool(source_url)
                        or bool(s.get("products"))
                    )
                    if not has_identity:
                        skipped += 1
                        continue

                    metadata_json = json.dumps(
                        {
                            "evidence": s.get("evidence", {}),
                            "source_urls": s.get("source_urls", []),
                            "products": s.get("products", []),
                            "product_categories": s.get("product_categories", []),
                        },
                        default=str,
                    )

                    await conn.execute(
                        """
                        INSERT INTO suppliers
                          (search_id, company_name, website, country, location,
                           moq, price, currency, metadata, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
                        """,
                        search_id,
                        name,
                        s.get("website") or source_url,
                        s.get("country"),
                        s.get("location") or s.get("city") or s.get("state"),
                        str(s.get("moq")) if s.get("moq") is not None else None,
                        str(s.get("price")) if s.get("price") is not None else None,
                        s.get("currency"),
                        metadata_json,
                    )
                    inserted += 1

            logger.info(
                "Persisted search %s with %d suppliers (%d skipped: no identity)",
                search_id, inserted, skipped,
            )
            return str(search_id)

        except Exception as exc:
            import traceback
            logger.error("Failed to persist search: %s", exc)
            logger.error(traceback.format_exc())
            return None

    async def _execute_search(self, plan: SearchPlan, limit: int = 20) -> List:
        """Execute all expanded queries and return raw results."""
        all_results: List = []
        for q in plan.expanded_queries[:5]:
            try:
                results = await self.router.search(q, limit=limit)
                all_results.extend(results)
            except Exception as e:
                logger.warning("Search failed for query %r: %s", q, e)
        return all_results

    async def _extract_suppliers(self, results: List, plan: SearchPlan) -> List[Any]:
        """Crawl, extract, and run supplier extraction."""
        deduped = self._deduplicate(results)
        ranked = self._rank(deduped, plan)
        top_urls = [r.url for r in ranked[: plan.max_pages]]

        safe_urls = [u for u in top_urls if is_safe_url(u)]
        if len(safe_urls) < len(top_urls):
            logger.warning(
                "Blocked %d unsafe URLs", len(top_urls) - len(safe_urls)
            )

        crawled = await self.crawler.crawl(safe_urls)
        extracted = self.extractor.extract(crawled)

        # Normalize dataclass or dict results
        extracted_dicts: List[Dict] = []
        for e in extracted:
            if isinstance(e, dict):
                extracted_dicts.append(e)
            else:
                extracted_dicts.append(
                    {
                        "url": getattr(e, "url", None),
                        "title": getattr(e, "title", ""),
                        "text": getattr(e, "text", ""),
                        "metadata": getattr(e, "metadata", {}),
                    }
                )

        # Choose implementation based on the AI flag.
        if getattr(settings, "AI_ENABLED", False):
            suppliers = self.llm.extract_suppliers(extracted_dicts)
        else:
            suppliers = self.extractor_iface.extract_batch(extracted_dicts)
        return suppliers

    def _enough_evidence(self, suppliers: List[Any], plan: SearchPlan) -> bool:
        if len(suppliers) < 3:
            return False
        for s in suppliers:
            if hasattr(s, "model_dump"):
                s = s.model_dump()
            if not isinstance(s, dict):
                continue
            if s.get("moq") or s.get("price"):
                return True
        return False

    async def _refine_plan(
        self, plan: SearchPlan, suppliers: List[Any]
    ) -> SearchPlan:
        # When AI is disabled, do not attempt LLM-based refinement.
        if not getattr(settings, "AI_ENABLED", False):
            return plan

        if not suppliers:
            new_q = f"{plan.original_query} supplier manufacturer"
            plan.expanded_queries = [new_q] + plan.expanded_queries[:2]
            return plan

        names = []
        for s in suppliers[:5]:
            if hasattr(s, "model_dump"):
                s = s.model_dump()
            if isinstance(s, dict):
                names.append(
                    s.get("name")
                    or s.get("company_name")
                    or s.get("supplier_name")
                    or "unknown"
                )

        prompt = (
            f"Original query: '{plan.original_query}'. "
            f"We found suppliers: {names}. "
            "Suggest a more specific search query to find additional relevant suppliers. "
            "Return only the query text, no explanation."
        )
        try:
            refined = self.llm._call_llm(
                LLMTask.SEARCH_REFINEMENT, prompt, max_tokens=50
            )
            plan.expanded_queries = [refined.strip()] + plan.expanded_queries[:2]
        except Exception as e:
            logger.warning("LLM refinement failed: %s; keeping original queries.", e)
        return plan

    # ------------------------------------------------------------------
    # Finalize + filter (operate on dicts at the pipeline boundary)
    # ------------------------------------------------------------------
    def _finalize(
        self,
        suppliers: List[Any],
        plan: SearchPlan,
        stop_reason: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not suppliers:
            return []

        # Normalize Pydantic models to dicts once, at the pipeline boundary.
        as_dicts: List[Dict[str, Any]] = []
        for s in suppliers:
            if isinstance(s, dict):
                as_dicts.append(s)
            elif hasattr(s, "model_dump"):
                as_dicts.append(s.model_dump())
            else:
                logger.debug("Skipping non-normalizable supplier: %r", type(s))
                continue

        filtered = self._apply_filters(as_dicts, plan)

        # Rank via interface.
        ranked = self.ranker_iface.rank(filtered, plan.constraints)

        final: List[Dict[str, Any]] = []
        for s in ranked:
            if hasattr(s, "model_dump"):
                s = s.model_dump()
            if not isinstance(s, dict):
                continue
            s["research_stopped_reason"] = stop_reason or "completed"
            final.append(s)
        return final

    def _apply_filters(
        self,
        suppliers: List[Dict[str, Any]],
        plan: SearchPlan,
    ) -> List[Dict[str, Any]]:
        constraints = plan.constraints or {}
        filtered: List[Dict[str, Any]] = []

        for s in suppliers:
            if hasattr(s, "model_dump"):
                s = s.model_dump()
            if not isinstance(s, dict):
                continue

            ok = True

            loc = constraints.get("location") or constraints.get("target_region")
            if loc:
                target = str(loc).lower()
                hay = " ".join(
                    str(s.get(f) or "").lower()
                    for f in ("country", "state", "city", "location", "address")
                )
                if hay.strip() and target not in hay:
                    ok = False

            if constraints.get("max_moq") and s.get("moq") is not None:
                try:
                    if int(s["moq"]) > int(constraints["max_moq"]):
                        ok = False
                except (TypeError, ValueError):
                    pass

            if constraints.get("max_price") and s.get("price") is not None:
                try:
                    if float(s["price"]) > float(constraints["max_price"]):
                        ok = False
                except (TypeError, ValueError):
                    pass

            if constraints.get("supplier_type") and s.get("supplier_type"):
                if str(s["supplier_type"]).lower() != str(
                    constraints["supplier_type"]
                ).lower():
                    ok = False

            if ok:
                filtered.append(s)

        return filtered

    def _build_response(
        self,
        suppliers: List[Any],
        plan: SearchPlan,
        stop_reason: str,
        db_search_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "search_id": db_search_id or self.request_id,
            "request_id": self.request_id,
            "query": plan.original_query,
            "plan": plan.model_dump() if hasattr(plan, "model_dump") else plan,
            "suppliers": suppliers,
            "answer": (
                self.answer_iface.generate(suppliers, plan)
                if suppliers
                else "No suppliers found."
            ),
            "research_stopped_reason": stop_reason,
            "evidence": [
                (s.get("evidence", {}) if isinstance(s, dict) else {})
                for s in suppliers
            ],
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _deduplicate(self, results: list) -> list:
        seen = set()
        deduped = []
        for r in results:
            if r.url not in seen:
                seen.add(r.url)
                deduped.append(r)
        return deduped

    def _rank(self, results: list, plan: SearchPlan) -> list:
        scored = []
        for r in results:
            score = 0
            title_words = set(r.title.lower().split())
            match = len(set(plan.keywords).intersection(title_words))
            score += match * 2
            if r.source_engine in ["google", "bing"]:
                score += 5
            elif r.source_engine == "duckduckgo":
                score += 3
            else:
                score += 1
            scored.append((score, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored]