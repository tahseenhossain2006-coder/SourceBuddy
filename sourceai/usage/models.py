from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserQuota(BaseModel):
    user_id: str
    daily_searches: int = 10
    daily_llm_calls: int = 20
    daily_llm_tokens: int = 50000
    daily_crawl_pages: int = 50
    monthly_llm_calls: int = 500
    monthly_crawl_pages: int = 1000

class UsageRecord(BaseModel):
    user_id: str
    request_id: str
    task: str
    provider: Optional[str]
    model: Optional[str]
    tokens_in: int = 0
    tokens_out: int = 0
    pages_crawled: int = 0
    extraction_calls: int = 0
    estimated_cost: Optional[float] = None
    timestamp: datetime = datetime.utcnow()
    status: str = "completed"