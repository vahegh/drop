from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from decorators import with_db
from db_models import TicketTier
from api_models import TicketTierCreate, TicketTierUpdate
from enums import PersonStatus


@with_db
async def get_tiers_for_event(db: AsyncSession, event_id: UUID) -> list[TicketTier]:
    result = await db.scalars(
        select(TicketTier)
        .where(TicketTier.event_id == event_id)
        .order_by(TicketTier.sort_order)
    )
    return result.all()


@with_db
async def get_tier(db: AsyncSession, tier_id: UUID) -> TicketTier | None:
    return await db.get(TicketTier, tier_id)


@with_db
async def create_tier(db: AsyncSession, event_id: UUID, body: TicketTierCreate) -> TicketTier:
    tier = TicketTier(event_id=event_id, **body.model_dump())
    db.add(tier)
    await db.commit()
    await db.refresh(tier)
    return tier


@with_db
async def update_tier(db: AsyncSession, tier_id: UUID, body: TicketTierUpdate) -> TicketTier:
    tier = await db.get(TicketTier, tier_id)
    if not tier:
        raise HTTPException(404, "Tier not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tier, field, value)
    db.add(tier)
    await db.commit()
    await db.refresh(tier)
    return tier


@with_db
async def delete_tier(db: AsyncSession, tier_id: UUID) -> None:
    tier = await db.get(TicketTier, tier_id)
    if not tier:
        raise HTTPException(404, "Tier not found")
    await db.delete(tier)
    await db.commit()


def resolve_tier_for_person(tiers: list[TicketTier], person_status: PersonStatus) -> TicketTier | None:
    now = datetime.now(timezone.utc)
    for tier in tiers:
        if not tier.is_active:
            continue
        if tier.required_person_status and tier.required_person_status != person_status:
            continue
        if tier.available_from and now < tier.available_from:
            continue
        if tier.available_until and now >= tier.available_until:
            continue
        return tier
    return None
