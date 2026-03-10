from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from decorators import with_db
from sqlalchemy.ext.asyncio import AsyncSession
from db_models import Payment
from services.payment import get_all_payments

router = APIRouter(tags=["Admin Payments"], prefix="/payments")


@router.get("")
async def list_payments():
    return await get_all_payments()


@router.delete("/{order_id}", status_code=204)
async def delete_payment_endpoint(order_id: int):
    return await _delete_payment(order_id)


@with_db
async def _delete_payment(db: AsyncSession, order_id: int):
    payment = await db.get(Payment, order_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    await db.delete(payment)
    await db.commit()
    return Response(status_code=204)
