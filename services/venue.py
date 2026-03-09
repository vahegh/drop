import asyncio
from uuid import UUID
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from decorators import with_db
from consts import VENUE_REVEAL_TEMPLATE
from services.templating import generate_template
from services.mailing import send_email, EmailRequest
from api_models import VenueCreate, VenueUpdate
from db_models import Venue, EventTicket, Person, MemberPass, Event


@with_db
async def get_all_venues(db: AsyncSession):
    venues = await db.scalars(select(Venue))
    return venues.all()


@with_db
async def get_venue_info(db: AsyncSession, id: UUID):
    venue = await db.get(Venue, id)
    if not venue:
        raise HTTPException(404, "Venue not found")
    return venue


@with_db
async def create_venue(db: AsyncSession, venue: VenueCreate):
    db_venue = Venue(
        name=venue.name,
        short_name=venue.short_name,
        address=venue.address,
        latitude=venue.latitude,
        longitude=venue.longitude,
        google_maps_link=venue.google_maps_link,
        yandex_maps_link=venue.yandex_maps_link,
    )
    db.add(db_venue)
    await db.commit()
    await db.refresh(db_venue)
    return db_venue


@with_db
async def update_venue(db: AsyncSession, id: UUID, venue: VenueUpdate):
    db_venue = await db.get(Venue, id)
    if not db_venue:
        raise HTTPException(404, "Venue not found")
    for field, value in venue.model_dump().items():
        if value:
            setattr(db_venue, field, value)
    await db.commit()
    await db.refresh(db_venue)
    return db_venue


@with_db
async def delete_venue(db: AsyncSession, id: UUID):
    db_venue = await db.get(Venue, id)
    if not db_venue:
        raise HTTPException(404, "Venue not found")
    await db.delete(db_venue)
    await db.commit()
    return
