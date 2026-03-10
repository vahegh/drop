from uuid import UUID
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from decorators import with_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db_models import Drink
from api_models import DrinkCreate, DrinkUpdate
from services.drink import get_all_drinks, create_drink

router = APIRouter(tags=["Admin Drinks"], prefix="/drinks")


@router.get("")
async def list_drinks():
    return await get_all_drinks()


@router.post("")
async def new_drink(body: DrinkCreate):
    drink = Drink(name=body.name, price=body.price)
    return await create_drink(drink)


@router.patch("/{id}")
async def update_drink(id: UUID, body: DrinkUpdate):
    return await _update_drink(id, body)


@with_db
async def _update_drink(db: AsyncSession, id: UUID, body: DrinkUpdate):
    drink = await db.get(Drink, id)
    if not drink:
        raise HTTPException(404, "Drink not found")
    if body.name is not None:
        drink.name = body.name
    if body.price is not None:
        drink.price = body.price
    await db.commit()
    await db.refresh(drink)
    return drink


@router.delete("/{id}", status_code=204)
async def delete_drink(id: UUID):
    return await _delete_drink(id)


@with_db
async def _delete_drink(db: AsyncSession, id: UUID):
    drink = await db.get(Drink, id)
    if not drink:
        raise HTTPException(404, "Drink not found")
    await db.delete(drink)
    await db.commit()
    return Response(status_code=204)
