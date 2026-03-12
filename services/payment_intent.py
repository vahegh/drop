from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from decorators import with_db
from db_models import Payment, PaymentIntent
from enums import PaymentStatus
from uuid import UUID


@with_db
async def create_payment_intent(db: AsyncSession, payment_intent: PaymentIntent):
    db.add(payment_intent)
    await db.commit()
    await db.refresh(payment_intent)
    return payment_intent


@with_db
async def delete_payment_intent(db: AsyncSession, order_id: int, recipient_id: UUID):
    await db.execute(delete(PaymentIntent).where(PaymentIntent.order_id == order_id).where(PaymentIntent.recipient_id == recipient_id))
    await db.commit()


@with_db
async def get_payment_intents(db: AsyncSession, order_id: int):
    payment_intents = await db.scalars(select(PaymentIntent).where(PaymentIntent.order_id == order_id))
    return payment_intents.all()


@with_db
async def get_payment_intent(db: AsyncSession, recipient_id: UUID):
    payment_intent = await db.scalar(select(PaymentIntent).where(PaymentIntent.recipient_id == recipient_id))
    return payment_intent


@with_db
async def get_confirmed_payment_intent(db: AsyncSession, recipient_id: UUID, event_id: UUID):
    payment_intent = await db.scalar(
        select(PaymentIntent)
        .join(Payment, PaymentIntent.order_id == Payment.order_id)
        .where(PaymentIntent.recipient_id == recipient_id)
        .where(Payment.event_id == event_id)
        .where(Payment.status == PaymentStatus.CONFIRMED)
    )
    return payment_intent
