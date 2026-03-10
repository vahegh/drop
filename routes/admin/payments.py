from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from decorators import with_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from db_models import Payment, PaymentIntent
from enums import PaymentStatus
from services.payment import get_all_payments, refund_payment

router = APIRouter(tags=["Admin Payments"], prefix="/payments")


@router.get("")
async def list_payments():
    return await get_all_payments()


@router.post("/{order_id}/refund")
@with_db
async def refund_payment_endpoint(db: AsyncSession, order_id: int):
    payment = await db.get(Payment, order_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    if payment.status != PaymentStatus.CONFIRMED:
        raise HTTPException(400, "Only CONFIRMED payments can be refunded")
    return await refund_payment(payment)


@router.delete("/{order_id}", status_code=204)
async def delete_payment_endpoint(order_id: int):
    return await _delete_payment(order_id)


@with_db
async def _delete_payment(db: AsyncSession, order_id: int):
    payment = await db.get(Payment, order_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    if payment.status != PaymentStatus.CREATED:
        raise HTTPException(400, "Only CREATED payments can be deleted")
    await db.execute(delete(PaymentIntent).where(PaymentIntent.order_id == order_id))
    await db.delete(payment)
    await db.commit()
    return Response(status_code=204)
