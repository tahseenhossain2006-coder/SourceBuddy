from fastapi import APIRouter, Depends, HTTPException
from sourceai.auth.dependencies import get_current_user
from sourceai.healthcheck import healthcheck

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

async def require_admin(user_id: str = Depends(get_current_user)):
    # Check if user is admin (we'll add a role column to users table)
    # For now, assume a simple check: we'll store is_admin boolean.
    # We'll implement a check via DB.
    # Placeholder: if not admin, raise 403.
    pass

@router.get("/health")
async def admin_health(user_id: str = Depends(require_admin)):
    result = await healthcheck()  # existing healthcheck returns dict
    return result

@router.get("/usage")
async def admin_usage(user_id: str = Depends(require_admin)):
    # Aggregate usage data from usage table
    return {"message": "usage data"}