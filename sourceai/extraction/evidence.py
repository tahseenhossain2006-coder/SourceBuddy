# sourceai/extraction/evidence.py
import hashlib
from datetime import datetime
from typing import Dict, Any, List

class EvidenceStore:
    """In-memory evidence store; persists via DB in production."""
    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def record(self, url: str, extracted: Dict[str, Any]):
        rec = {
            "source_url": url,
            "extracted_at": datetime.utcnow().isoformat(),
            "engine": extracted.get("extraction_engine", "unknown"),
            "content_hash": hashlib.sha256(
                (extracted.get("text") or "").encode()
            ).hexdigest()[:16],
            "fields": {
                k: v for k, v in extracted.items()
                if k not in {"text"}
            },
        }
        self._records.append(rec)

    def all(self) -> List[Dict[str, Any]]:
        return list(self._records)