# sourceai/auth/router.py
import logging

from fastapi import APIRouter, Depends, HTTPException

from .models import (
    UserCreate,
    UserLogin,
    RefreshRequest,
    PasswordChange,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserResponse,
)
from .service import AuthService
from sourceai.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post("/register")
async def register(user: UserCreate):
    try:
        return await auth_service.register(user)
    except Exception:
        logger.exception(
            "Registration failed for %s", getattr(user, "email", "?")
        )
        raise HTTPException(status_code=400, detail="Registration failed")


@router.post("/login")
async def login(credentials: UserLogin):
    try:
        return await auth_service.login(credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/refresh")
async def refresh(req: RefreshRequest):
    try:
        return await auth_service.refresh_token(req.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.get("/me", response_model=UserResponse)
async def me(user_id: str = Depends(get_current_user)):
    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user