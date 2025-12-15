from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from decorators import with_db
from db_models import PaymentIntent


@with_db
async def create_payment_intent(db: AsyncSession, payment_intent: PaymentIntent):
    db.add(payment_intent)
    await db.commit()
    await db.refresh(payment_intent)
    return payment_intent


@with_db
async def delete_payment_intents(db: AsyncSession, order_id: int):
    await db.execute(delete(PaymentIntent).where(PaymentIntent.order_id == order_id))
    await db.commit()


@with_db
async def get_payment_intents(db: AsyncSession, order_id: int):
    payment_intents = await db.scalars(select(PaymentIntent).where(PaymentIntent.order_id == order_id))
    return payment_intents.all()
