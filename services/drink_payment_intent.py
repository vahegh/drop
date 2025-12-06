from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from decorators import with_db
from db_models import DrinkPaymentIntent


@with_db
async def create_drink_payment_intent(db: AsyncSession, drink_payment_intent: DrinkPaymentIntent):
    db.add(drink_payment_intent)
    await db.commit()
    await db.refresh(drink_payment_intent)
    return drink_payment_intent


@with_db
async def get_drink_payments_intents(db: AsyncSession, order_id: int):
    drink_payment_intents = await db.scalars(select(DrinkPaymentIntent).where(DrinkPaymentIntent.order_id == order_id))
    return drink_payment_intents.all()


@with_db
async def delete_drink_payment_intents(db: AsyncSession, order_id: int):
    await db.execute(delete(DrinkPaymentIntent).where(DrinkPaymentIntent.order_id == order_id))
