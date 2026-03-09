from fastapi import APIRouter, Request
from decorators import verify_admin_token
from services.payment import get_all_payments

router = APIRouter(tags=["Admin Payments"], prefix="/payments")


@router.get("")
async def list_payments(request: Request):
    await verify_admin_token(request)
    return await get_all_payments()
