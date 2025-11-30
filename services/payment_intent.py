from sqlalchemy.ext.asyncio import AsyncSession
from decorators import with_db
from db_models import PaymentIntent


@with_db
async def create_payment_intent(db: AsyncSession, payment_intent: PaymentIntent):
    db.add(payment_intent)
    await db.commit()
    await db.refresh(payment_intent)
    return payment_intent
