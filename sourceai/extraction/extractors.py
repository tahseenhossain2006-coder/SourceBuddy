# sourceai/extraction/extractors.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TrafilaturaExtractor:
    name = "trafilatura"
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        try:
            import trafilatura
            text = trafilatura.extract(html) or ""
            return {"url": url, "text": text, "title": ""}
        except ImportError:
            return None

class BeautifulSoupExtractor:
    name = "beautifulsoup"
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for t in soup(["script", "style", "nav", "footer"]):
            t.decompose()
        text = soup.get_text(separator=" ", strip=True)
        title = soup.title.string if soup.title else ""
        return {"url": url, "text": text[:20000], "title": title}

class ReadabilityExtractor:
    name = "readability"
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        try:
            from readability import Document
            doc = Document(html)
            return {"url": url, "text": doc.summary(), "title": doc.title()}
        except ImportError:
            return None