# sourceai/crawling/manager.py
import asyncio
import aiohttp
import logging
from typing import List, Optional
from dataclasses import dataclass
from urllib.parse import urljoin

from sourceai.security.url_validator import is_safe_url
from sourceai.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    url: str
    html: Optional[str]
    status: int
    error: Optional[str] = None
    content_type: Optional[str] = None
    bytes: int = 0


class CrawlManager:
    def __init__(
        self,
        max_concurrent: Optional[int] = None,
        timeout: Optional[int] = None,
        max_size: Optional[int] = None,
        max_redirects: int = 5,
    ):
        self.max_concurrent = max_concurrent or settings.CRAWL_CONCURRENCY
        self.timeout = timeout or settings.CRAWL_TIMEOUT
        self.max_size = max_size or settings.MAX_PAGE_BYTES
        self.max_redirects = max_redirects

    async def crawl(self, urls: List[str]) -> List[CrawlResult]:
        safe = []
        for u in urls:
            if is_safe_url(u):
                safe.append(u)
            else:
                logger.warning(f"Blocked unsafe URL: {u}")

        if not safe:
            return []

        semaphore = asyncio.Semaphore(self.max_concurrent)
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={"User-Agent": settings.CRAWL_USER_AGENT},
        ) as session:
            tasks = [self._fetch(session, url, semaphore) for url in safe]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        out: List[CrawlResult] = []
        for r in results:
            if isinstance(r, CrawlResult):
                out.append(r)
        return out

    async def _fetch(self, session, url: str, semaphore) -> CrawlResult:
        async with semaphore:
            try:
                current = url
                for _ in range(self.max_redirects):
                    if not is_safe_url(current):
                        return CrawlResult(
                            url=url, html=None, status=0,
                            error=f"Unsafe redirect to {current}",
                        )
                    async with session.get(current, allow_redirects=False) as resp:
                        if 300 <= resp.status < 400 and "location" in resp.headers:
                            current = urljoin(current, resp.headers["location"])
                            continue

                        ctype = resp.headers.get("content-type", "")
                        if not any(
                            t in ctype.lower()
                            for t in ["text/html", "application/xhtml", "text/plain"]
                        ):
                            return CrawlResult(
                                url=url, html=None, status=resp.status,
                                content_type=ctype,
                                error="Unsupported content type",
                            )

                        html_parts = []
                        total = 0
                        too_large = False
                        async for chunk in resp.content.iter_chunked(8192):
                            total += len(chunk)
                            if total > self.max_size:
                                too_large = True
                                break
                            html_parts.append(chunk)

                        if too_large:
                            logger.warning(
                                "Crawl rejected oversized response %s (%d > %d)",
                                url, total, self.max_size,
                            )
                            return CrawlResult(
                                url=url, html=None, status=resp.status,
                                content_type=ctype, bytes=total,
                                error=f"Response too large ({total} > {self.max_size})",
                            )

                        html = b"".join(html_parts).decode("utf-8", errors="replace")

                        if self._needs_playwright(html):
                            rendered = await self._playwright_render(url)
                            if rendered:
                                html = rendered

                        return CrawlResult(
                            url=url, html=html, status=resp.status,
                            content_type=ctype, bytes=total,
                        )

                return CrawlResult(
                    url=url, html=None, status=0, error="Too many redirects",
                )

            except asyncio.TimeoutError:
                return CrawlResult(url=url, html=None, status=0, error="Timeout")
            except Exception as e:
                logger.warning(f"Crawl failed {url}: {e}")
                return CrawlResult(url=url, html=None, status=0, error=str(e))

    def _needs_playwright(self, html: str) -> bool:
        if len(html) < 500:
            return True
        lower = html.lower()
        return (
            '<div id="app"' in lower
            or "<div id='app'" in lower
            or "ng-app" in lower
            or "__next_data__" in lower
        )

    async def _playwright_render(self, url: str) -> Optional[str]:
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    page = await browser.new_page()
                    await page.goto(
                        url,
                        timeout=self.timeout * 1000,
                        wait_until="networkidle",
                    )
                    return await page.content()
                finally:
                    await browser.close()
        except Exception as e:
            logger.warning(f"Playwright render failed {url}: {e}")
            return None