from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class QuoteCreate(BaseModel):
    rfq_id: str
    supplier_id: str
    price: float
    currency: str
    moq: Optional[int] = None
    lead_time: Optional[str] = None
    payment_terms: Optional[str] = None
    shipping_terms: Optional[str] = None
    incoterms: Optional[str] = None
    validity: Optional[datetime] = None
    notes: Optional[str] = None
    evidence: Optional[dict] = None

class QuoteResponse(BaseModel):
    id: str
    rfq_id: str
    supplier_id: str
    price: float
    currency: str
    moq: Optional[int]
    lead_time: Optional[str]
    payment_terms: Optional[str]
    shipping_terms: Optional[str]
    incoterms: Optional[str]
    validity: Optional[datetime]
    notes: Optional[str]
    evidence: Optional[dict]
    created_at: datetime