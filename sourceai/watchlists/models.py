from pydantic import BaseModel
from typing import Optional
from enum import Enum

class WatchType(str, Enum):
    SUPPLIER = "supplier"
    PRODUCT = "product"
    PRICE = "price"
    MOQ = "moq"
    RFQ = "rfq"

class WatchlistCreate(BaseModel):
    type: WatchType
    target_id: str  # supplier_id, product_id, etc.
    condition: Optional[str] = None  # e.g., "price < 100"

class WatchlistResponse(BaseModel):
    id: str
    user_id: str
    type: WatchType
    target_id: str
    condition: Optional[str]
    created_at: str
class WatchlistCheckResult(BaseModel):
    """Returned by POST /watchlists/{id}/check."""
    watchlist_id: str
    changed: bool
    alert_created: bool
    last_hash: str
    checked_at: str
    error: Optional[str] = None
class WatchlistResponse(BaseModel):
    id: str
    user_id: str
    type: WatchType
    target_id: str
    condition: Optional[str] = None
    last_hash: Optional[str] = None
    last_checked: Optional[str] = None
    created_at: str        