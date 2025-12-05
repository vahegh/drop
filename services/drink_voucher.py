import logging
from uuid import UUID
from sqlalchemy import select
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from decorators import with_db
from db_models import DrinkVoucher

logger = logging.getLogger(__name__)


@with_db
async def create_drink_voucher(db: AsyncSession, drink_voucher: DrinkVoucher):
    db.add(drink_voucher)
    await db.commit()
    await db.refresh(drink_voucher)
    return drink_voucher


@with_db
async def get_all_drink_vouchers(db: AsyncSession):
    drink_vouchers = await db.scalars(select(DrinkVoucher))
    return drink_vouchers.all()


@with_db
async def get_drink_vouchers_by_person_id(db: AsyncSession, person_id: UUID):
    result = await db.scalars(select(DrinkVoucher).where(DrinkVoucher.person_id == person_id))
    return result.all()


@with_db
async def get_drink_voucher(db: AsyncSession, id: UUID):
    drink_voucher = await db.get(DrinkVoucher, id)
    if not drink_voucher:
        raise HTTPException(404, "Drink voucher not found")
    return drink_voucher


@with_db
async def delete_drink_voucher(db: AsyncSession, id: UUID):
    drink_voucher = await db.get(DrinkVoucher, id)
    if not drink_voucher:
        raise HTTPException(404, "Drink voucher not found")
    await db.delete(drink_voucher)
    await db.commit()
    return


@with_db
async def redeem_drink_voucher(db: AsyncSession, id: UUID):
    drink_voucher = await db.get(DrinkVoucher, id)
    if not drink_voucher:
        raise HTTPException(404, "Drink voucher not found")
    drink_voucher.used_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(drink_voucher)
    return drink_voucher
