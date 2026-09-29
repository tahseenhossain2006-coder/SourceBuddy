from fastapi import APIRouter, Depends, HTTPException
from sourceai.auth.dependencies import get_current_user
from sourceai.rfq.service import RFQService
from sourceai.rfq.models import RFQCreate, RFQResponse, RFQStatus

router = APIRouter(prefix="/api/v1/rfqs", tags=["rfq"])

@router.post("/", response_model=RFQResponse)
async def create_rfq(data: RFQCreate, user_id: str = Depends(get_current_user)):
    service = RFQService()
    try:
        return await service.create_rfq(user_id, data)
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/{rfq_id}", response_model=RFQResponse)
async def get_rfq(rfq_id: str, user_id: str = Depends(get_current_user)):
    service = RFQService()
    rfq = await service.get_rfq(rfq_id, user_id)
    if not rfq:
        raise HTTPException(404, "RFQ not found")
    return rfq

@router.patch("/{rfq_id}/status")
async def update_rfq_status(rfq_id: str, status: RFQStatus, user_id: str = Depends(get_current_user)):
    service = RFQService()
    if not await service.update_status(rfq_id, user_id, status):
        raise HTTPException(404, "RFQ not found")
    return {"status": "updated"}