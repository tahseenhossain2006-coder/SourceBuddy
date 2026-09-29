from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class RFQStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENDING = "sending"
    SENT = "sent"
    WAITING = "waiting"
    PARTIAL_RESPONSE = "partial_response"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class RFQItem(BaseModel):
    product_name: str
    quantity: int
    unit: str
    specifications: Optional[Dict[str, Any]] = None
    target_price: Optional[float] = None
    target_moq: Optional[int] = None

class RFQCreate(BaseModel):
    title: str
    description: Optional[str] = None
    items: List[RFQItem]
    suppliers: List[str]  # supplier IDs
    deadline: Optional[datetime] = None
    delivery_location: Optional[str] = None
    currency: str = "USD"

class RFQResponse(BaseModel):
    id: str
    user_id: str
    title: str
    status: RFQStatus
    items: List[RFQItem]
    suppliers: List[str]
    deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None