from typing import Dict, Any

class ExtractionQuality:
    @staticmethod
    def is_sufficient(extracted: Dict[str, Any]) -> bool:
        if not extracted:
            return False
        if not extracted.get("source_url") and not extracted.get("url"):
            return False
        has_company = bool(extracted.get("company_name"))
        has_product = bool(extracted.get("product"))
        has_text = len(extracted.get("text") or "") > 200
        has_evidence = bool(extracted.get("evidence"))
        if has_company or has_product or has_text or has_evidence:
            return True
        if isinstance(extracted.get("suppliers"), list) and extracted["suppliers"]:
            return True
        return False