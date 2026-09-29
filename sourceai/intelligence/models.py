# sourceai/intelligence/models.py
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

# ---------- Common Enums ----------
class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_SUPPORTED = "not_supported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"

class ConfidenceLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class ImportanceLevel(str, Enum):
    CRITICAL = "critical"
    IMPORTANT = "important"
    OPTIONAL = "optional"

class FilterOperator(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"

# ---------- Evidence Verification ----------
class EvidenceItem(BaseModel):
    field: str
    value: Any
    source_url: str
    supporting_text: Optional[str] = None
    status: VerificationStatus
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)

class EvidenceVerificationResult(BaseModel):
    items: List[EvidenceItem]
    overall_status: VerificationStatus
    overall_confidence: float = Field(ge=0.0, le=1.0)

# ---------- Confidence Analysis ----------
class ConfidenceAnalysis(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    level: ConfidenceLevel
    reasoning: str
    supporting_factors: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)

# ---------- Missing Data Reasoning ----------
class MissingDataReason(BaseModel):
    field: str
    reason: str
    importance: ImportanceLevel
    likely_source: Optional[str] = None
    recommended_action: str

class MissingDataAnalysis(BaseModel):
    missing_fields: List[MissingDataReason]

# ---------- Filtering ----------
class FilterCondition(BaseModel):
    field: str
    operator: FilterOperator
    value: Any = None
    unit: Optional[str] = None

class FilterExpression(BaseModel):
    conditions: List[FilterCondition]
    logic: str = "AND"  # or "OR", "NOT"

# ---------- Supplier Comparison ----------
class ComparisonField(BaseModel):
    field: str
    values: Dict[str, Any]  # supplier_id -> value
    unit: Optional[str] = None
    winner_id: Optional[str] = None
    explanation: Optional[str] = None

class SupplierComparison(BaseModel):
    supplier_ids: List[str]
    fields: List[ComparisonField]
    winner_by_field: Dict[str, str]  # field -> supplier_id
    overall_recommendation: Optional[str] = None
    tradeoffs: List[str] = Field(default_factory=list)
    reasoning: str

# ---------- Unified Request ----------
class IntelligenceRequest(BaseModel):
    supplier_records: List[Dict[str, Any]]  # raw supplier data
    user_query: str
    filters: Optional[List[str]] = None  # raw filter strings
    enable_evidence_verification: bool = True
    enable_confidence_analysis: bool = True
    enable_missing_data_reasoning: bool = True
    enable_nl_filtering: bool = True
    enable_comparison: bool = True
    comparison_limit: int = 3

class IntelligenceResponse(BaseModel):
    verified_suppliers: List[Dict[str, Any]]
    evidence_results: Optional[List[EvidenceVerificationResult]] = None  # ✅ Fixed: List of results
    confidence_results: Optional[List[ConfidenceAnalysis]] = None
    missing_data_results: Optional[List[MissingDataAnalysis]] = None
    filtered_suppliers: Optional[List[Dict[str, Any]]] = None
    comparison: Optional[SupplierComparison] = None