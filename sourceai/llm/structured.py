# sourceai/llm/structured.py
from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class RequirementResult(BaseModel):
    product: Optional[str] = None
    quantity: Optional[int] = None
    budget_per_unit: Optional[float] = None
    total_budget: Optional[float] = None
    currency: Optional[str] = None
    target_country: Optional[str] = None
    target_region: Optional[str] = None
    target_city: Optional[str] = None
    moq: Optional[int] = None
    supplier_type: Optional[str] = None
    customization_required: Optional[bool] = None
    certifications: List[str] = Field(default_factory=list)
    shipping_destination: Optional[str] = None
    required_delivery_time: Optional[str] = None
    location_hint: Optional[str] = None


class SupplierExtractionResult(BaseModel):
    supplier_name: Optional[str] = None
    company_name: Optional[str] = None
    website: Optional[str] = None
    domain: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    supplier_type: Optional[str] = None
    supplier_type_signals: List[str] = Field(default_factory=list)
    manufacturer_status: Optional[str] = None
    products: List[str] = Field(default_factory=list)
    product_categories: List[str] = Field(default_factory=list)
    moq: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    certifications: List[str] = Field(default_factory=list)
    years_in_business: Optional[int] = None
    factory_information: Optional[str] = None
    capacity: Optional[str] = None
    shipping_regions: List[str] = Field(default_factory=list)
    payment_terms: Optional[str] = None
    source_urls: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    data_completeness: float = 0.0
    confidence: float = 0.0

    @model_validator(mode="before")
    @classmethod
    def _unwrap_list(cls, data: Any) -> Any:
        """
        The LLM sometimes wraps the object in a single-element list, or
        splits it across multiple dicts in a list. Merge or unwrap so
        validation succeeds.
        """
        if isinstance(data, list):
            if len(data) == 1 and isinstance(data[0], dict):
                return data[0]
            if data and all(isinstance(x, dict) for x in data):
                merged: Dict[str, Any] = {}
                for item in data:
                    for k, v in item.items():
                        merged.setdefault(k, v)
                return merged
        return data

    @field_validator(
        "products",
        "product_categories",
        "certifications",
        "shipping_regions",
        "supplier_type_signals",
        mode="before",
    )
    @classmethod
    def _stringify_list(cls, v: Any) -> Any:
        """
        Coerce list items to strings. The LLM often returns rich dicts like
        {'category': 'Steel', 'usage': 'Home'} where the schema wants flat
        strings. Preserve the most useful text and drop the rest.
        """
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if not isinstance(v, list):
            return [str(v)]
        out: List[str] = []
        for item in v:
            if isinstance(item, str):
                s = item.strip()
                if s:
                    out.append(s)
            elif isinstance(item, dict):
                for key in ("category", "name", "product", "title"):
                    val = item.get(key)
                    if isinstance(val, str) and val.strip():
                        out.append(val.strip())
                        break
                else:
                    joined = ", ".join(
                        str(val) for val in item.values() if val
                    ).strip()
                    if joined:
                        out.append(joined)
            else:
                s = str(item).strip()
                if s:
                    out.append(s)
        return out


class ProductExtractionResult(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    specifications: Dict[str, Any] = Field(default_factory=dict)
    variants: List[str] = Field(default_factory=list)
    price: Optional[float] = None
    currency: Optional[str] = None
    moq: Optional[int] = None
    unit: Optional[str] = None
    materials: List[str] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    sizes: List[str] = Field(default_factory=list)
    brand: Optional[str] = None
    supplier: Optional[str] = None
    source_url: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0


class EvidenceItem(BaseModel):
    field: str
    value: Any
    source_url: str
    excerpt: Optional[str] = None
    confidence: float = 0.5


class EntityResolutionResult(BaseModel):
    same_entity: bool
    confidence: float
    reasons: List[str] = Field(default_factory=list)
    source_entities: List[str] = Field(default_factory=list)


class ReconciliationResult(BaseModel):
    field: str
    values: Dict[str, Any]  # source_id -> value
    conflict: bool
    preferred_value: Optional[Any] = None
    confidence: float
    reason: str


class ContradictionResult(BaseModel):
    field: str
    source_a: str
    value_a: Any
    source_b: str
    value_b: Any
    conflict_type: str
    explanation: str


class RiskAnalysisResult(BaseModel):
    risk_level: str
    risk_factors: List[str] = Field(default_factory=list)
    positive_signals: List[str] = Field(default_factory=list)
    recommendation: str
    evidence: Dict[str, Any] = Field(default_factory=dict)


class ComparisonResult(BaseModel):
    supplier_ids: List[str]
    fields: Dict[str, Dict[str, Any]]
    winner_by_field: Dict[str, str]
    overall_recommendation: Optional[str] = None
    tradeoffs: List[str] = Field(default_factory=list)
    reasoning: str