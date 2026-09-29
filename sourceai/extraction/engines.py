from bs4 import BeautifulSoup
from typing import Dict, Any

class TrafilaturaExtractor:
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        import trafilatura
        text = trafilatura.extract(html)
        return {
            "url": url,
            "title": "",
            "text": text or "",
            "metadata": {},
            "extraction_method": "trafilatura",
        }

class BeautifulSoupExtractor:
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=" ", strip=True)
        title = soup.title.string if soup.title else ""
        return {
            "url": url,
            "title": title,
            "text": text[:5000],
            "metadata": {},
            "extraction_method": "beautifulsoup",
        }

class ReadabilityExtractor:
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        from readability import Document
        doc = Document(html)
        return {
            "url": url,
            "title": doc.title(),
            "text": doc.summary(),
            "metadata": {},
            "extraction_method": "readability",
        }