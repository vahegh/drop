import logging
from sqlalchemy import select
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from db_models import CardBinding
from api_models import CardBindingCreate, CardBindingUpdate
from decorators import with_db

logger = logging.getLogger(__name__)


@with_db
async def create_card_binding(db: AsyncSession, request: CardBindingCreate):
    card_binding = CardBinding(**request.model_dump())
    db.add(card_binding)
    await db.commit()
    await db.refresh(card_binding)
    return card_binding


@with_db
async def update_card_binding(db: AsyncSession, id: UUID, request: CardBindingUpdate):
    card_binding = await db.get(CardBinding, id)
    if not card_binding:
        raise HTTPException(404, "Binding not found")

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(card_binding, field, value)

    await db.commit()
    await db.refresh(card_binding)
    return card_binding


@with_db
async def get_card_binding_by_person_id(db: AsyncSession, person_id: UUID):
    bindings = await db.scalars(select(CardBinding).where(CardBinding.person_id == person_id))
    return bindings.all()
