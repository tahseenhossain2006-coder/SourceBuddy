from pydantic import BaseModel
from enum import Enum

class AlertType(str, Enum):
    PRICE_CHANGE = "price_change"
    MOQ_CHANGE = "moq_change"
    SUPPLIER_CHANGE = "supplier_change"
    NEW_SUPPLIER = "new_supplier"
    QUOTE_RECEIVED = "quote_received"
    RFQ_RESPONSE = "rfq_response"

class AlertResponse(BaseModel):
    id: str
    user_id: str
    type: AlertType
    message: str
    data: dict
    read: bool
    created_at: str