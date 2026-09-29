# sourceai/alerts/routes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from sourceai.auth.dependencies import get_current_user
from sourceai.alerts.service import AlertService
from sourceai.alerts.models import AlertResponse

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(user_id: str = Depends(get_current_user)):
    return await AlertService().get_unread(user_id)


@router.post("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    user_id: str = Depends(get_current_user),
):
    marked = await AlertService().mark_read(alert_id, user_id)
    if not marked:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "read"}