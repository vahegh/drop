from fastapi import APIRouter
from services.payment import get_all_payments

router = APIRouter(tags=["Admin Payments"], prefix="/payments")


@router.get("")
async def list_payments():
    return await get_all_payments()
