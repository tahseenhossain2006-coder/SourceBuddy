# sourceai/watchlists/routes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from sourceai.auth.dependencies import get_current_user
from sourceai.watchlists.service import WatchlistService
from sourceai.watchlists.models import WatchlistCreate, WatchlistResponse
from sourceai.watchlists.models import WatchlistCheckResult

router = APIRouter(prefix="/api/v1/watchlists", tags=["watchlists"])


@router.post("/", response_model=WatchlistResponse)
async def create_watchlist(
    data: WatchlistCreate,
    user_id: str = Depends(get_current_user),
):
    try:
        return await WatchlistService().create(user_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[WatchlistResponse])
async def list_watchlists(user_id: str = Depends(get_current_user)):
    return await WatchlistService().get_all(user_id)


@router.delete("/{watch_id}")
async def delete_watchlist(
    watch_id: str,
    user_id: str = Depends(get_current_user),
):
    deleted = await WatchlistService().delete(watch_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {"status": "deleted"}
@router.post("/{watch_id}/check", response_model=WatchlistCheckResult)
async def check_watchlist(
    watch_id: str,
    user_id: str = Depends(get_current_user),
):
    try:
        return await WatchlistService().check(watch_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Check failed")