import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from decorators import with_db
from db_models import Drink

logger = logging.getLogger(__name__)


@with_db
async def create_drink(db: AsyncSession, drink: Drink):
    db.add(drink)
    await db.commit()
    await db.refresh(drink)
    return drink


@with_db
async def get_all_drinks(db: AsyncSession):
    drinks = await db.scalars(select(Drink))
    return drinks.all()


@with_db
async def get_drink(db: AsyncSession, id: UUID):
    return await db.get(Drink, id)
