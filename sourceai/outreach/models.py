from pydantic import BaseModel
from typing import Optional
from enum import Enum

class OutreachStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    REPLIED = "replied"

class OutreachCreate(BaseModel):
    rfq_id: str
    supplier_id: str
    message: str
    subject: str
    cc: Optional[str] = None

class OutreachResponse(BaseModel):
    id: str
    rfq_id: str
    supplier_id: str
    status: OutreachStatus
    message: str
    subject: str
    sent_at: Optional[str] = None
    created_at: str