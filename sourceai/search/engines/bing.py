"""Bing search via Playwright headless Chromium."""
import base64
import logging
from typing import List
from urllib.parse import parse_qs, quote_plus, urlparse

from .base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


def _unwrap_bing_url(url: str) -> str:
    """
    Bing wraps result URLs in a redirector:
        https://www.bing.com/ck/a?...&u=a1<base64>&ntb=1
    Decode the `u` parameter to recover the real destination.
    If the URL is already a plain URL, return it unchanged.
    """
    if not url:
        return url
    try:
        parsed = urlparse(url)
        if "bing.com/ck/a" not in parsed.netloc + parsed.path:
            return url
        qs = parse_qs(parsed.query)
        u = qs.get("u", [None])[0]
        if not u:
            return url
        # Bing prefixes the base64 with "a1" before the real payload
        if u.startswith("a1"):
            u = u[2:]
        padded = u + "=" * (-len(u) % 4)
        decoded = base64.urlsafe_b64decode(padded).decode("utf-8", "ignore")
        return decoded or url
    except Exception:
        return url


class BingEngine(SearchEngine):
    name = "bing"

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

        url = (
            f"https://www.bing.com/search?q={quote_plus(query)}"
            f"&count={limit}&setlang=en"
        )
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
                try:
                    await page.wait_for_selector(
                        "#b_results li.b_algo", timeout=8000
                    )
                except Exception:
                    logger.info("Bing results not rendered in time")
                    return []

                items = await page.query_selector_all("#b_results li.b_algo")
                for it in items:
                    if len(results) >= limit:
                        break
                    a = await it.query_selector("h2 a")
                    if not a:
                        continue
                    title = (await a.inner_text()).strip()
                    href = await a.get_attribute("href") or ""
                    href = _unwrap_bing_url(href)
                    if not href or not href.startswith("http"):
                        continue
                    snippet = ""
                    sn = await it.query_selector(".b_caption p, p")
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