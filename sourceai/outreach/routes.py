# sourceai/rfq/routes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from sourceai.auth.dependencies import get_current_user
from sourceai.rfq.service import RFQService
from sourceai.rfq.models import RFQCreate, RFQResponse, RFQStatus

router = APIRouter(prefix="/api/v1/outreach", tags=["outreach"])


@router.post("/", response_model=RFQResponse)
async def create_rfq(data: RFQCreate, user_id: str = Depends(get_current_user)):
    try:
        return await RFQService().create_rfq(user_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[RFQResponse])
async def list_rfqs(user_id: str = Depends(get_current_user)):
    return await RFQService().list_rfqs(user_id)


@router.get("/{rfq_id}", response_model=RFQResponse)
async def get_rfq(rfq_id: str, user_id: str = Depends(get_current_user)):
    rfq = await RFQService().get_rfq(rfq_id, user_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return rfq


@router.patch("/{rfq_id}/status", response_model=RFQResponse)
async def update_rfq_status(
    rfq_id: str,
    status: RFQStatus,
    user_id: str = Depends(get_current_user),
):
    try:
        return await RFQService().transition(rfq_id, user_id, status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{rfq_id}")
async def delete_rfq(rfq_id: str, user_id: str = Depends(get_current_user)):
    if not await RFQService().delete_rfq(rfq_id, user_id):
        raise HTTPException(status_code=404, detail="RFQ not found")
    return {"status": "deleted"}