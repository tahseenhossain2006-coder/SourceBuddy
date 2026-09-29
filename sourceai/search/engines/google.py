"""Google search via Playwright headless Chromium."""
import logging
from typing import List
from urllib.parse import quote_plus

from .base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class GoogleEngine(SearchEngine):
    name = "google"

    def __init__(self, timeout: float = 25.0, headless: bool = True):
        super().__init__()
        self.timeout = timeout
        self.headless = headless

    async def _search(self, query: str, limit: int) -> List[SearchResult]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright not installed")
            return []

        url = f"https://www.google.com/search?q={quote_plus(query)}&num={limit}&hl=en"
        results: List[SearchResult] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            try:
                ctx = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0 Safari/537.36"
                    ),
                    locale="en-US",
                )
                page = await ctx.new_page()
                await page.goto(
                    url, timeout=int(self.timeout * 1000),
                    wait_until="domcontentloaded",
                )
                html = await page.content()
                if "consent.google.com" in page.url or "unusual traffic" in html.lower():
                    logger.warning("Google blocked (consent/captcha)")
                    return []

                blocks = await page.query_selector_all("div.MjjYud, div.g")
                for blk in blocks:
                    if len(results) >= limit:
                        break
                    a = await blk.query_selector("a[href^='http']")
                    h3 = await blk.query_selector("h3")
                    if not a or not h3:
                        continue
                    title = (await h3.inner_text()).strip()
                    href = await a.get_attribute("href")
                    if not href or not href.startswith("http"):
                        continue
                    snippet = ""
                    sn = await blk.query_selector("div.VwiC3b, div.IsZvec, span.aCOpRe")
                    if sn:
                        snippet = (await sn.inner_text()).strip()[:300]
                    results.append(SearchResult(
                        title=title, url=href, snippet=snippet,
                        source_engine=self.name, query=query,
                    ))
            finally:
                await browser.close()
        return results

    async def _health_check(self) -> bool:
        try:
            res = await self._search("test", 1)
            return len(res) > 0
        except Exception:
            return False