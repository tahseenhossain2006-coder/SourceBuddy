from fastapi import Request, HTTPException
from .service import UsageService
import uuid

usage_service = UsageService()

async def usage_middleware(request: Request, call_next):
    user_id = request.state.user_id if hasattr(request.state, "user_id") else None
    if user_id and request.url.path.startswith("/api/v1/search"):
        # Reserve search quota
        if not await usage_service.check_and_reserve(user_id, "search"):
            raise HTTPException(429, "Daily search limit reached")
    response = await call_next(request)
    return response