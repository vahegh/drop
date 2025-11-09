import asyncio
from uuid import UUID
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from decorators import with_db
from consts import VENUE_REVEAL_TEMPLATE
from services.templating import generate_template
from services.mailing import send_email, EmailRequest
from api_models import VenueCreate, VenueResponse, VenueUpdate
from db_models import Venue, EventTicket, Person, MemberPass, Event

router = APIRouter(tags=['Venue'], prefix="/api/venue")


# @router.get("/all", response_model=list[VenueResponse])
@with_db
async def get_all_venues(db: AsyncSession):
    venues = await db.scalars(select(Venue))
    return venues.all()


# @router.get("/{id}", response_model=VenueResponse)
@with_db
async def get_venue_info(db: AsyncSession, id: UUID):
    venue = await db.get(Venue, id)
    if not venue:
        raise HTTPException(404, "Venue not found")
    return venue


# @router.post("/", response_model=VenueResponse)
@with_db
async def create_venue(db: AsyncSession, venue: VenueCreate):
    db_venue = Venue(
        name=venue.name,
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


# @router.put("/{id}", response_model=VenueResponse)
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


# @router.delete("/{id}")
@with_db
async def delete_venue(db: AsyncSession, id: UUID):
    db_venue = await db.get(Venue, id)
    if not db_venue:
        raise HTTPException(404, "Venue not found")
    await db.delete(db_venue)
    await db.commit()
    return


# @router.post("/venue-reveal")
@with_db
async def venue_reveal(db: AsyncSession, event_id: UUID):
    event = await db.get(Event, event_id)
    venue = await db.get(Venue, event.venue_id)
    context = {
        "event_name": event.name,
        "venue_name": venue.name,
        "address": venue.address,
        "google_maps_link": venue.google_maps_link,
        "yandex_maps_link": venue.yandex_maps_link
    }

    persons = (
        await db.scalars(
            select(Person)
            .outerjoin(EventTicket, EventTicket.person_id == Person.id)
            .outerjoin(MemberPass, MemberPass.person_id == Person.id)
            .where(
                or_(
                    EventTicket.event_id == event.id,
                    MemberPass.id.isnot(None)
                )
            )
            .distinct()
        )
    ).all()

    print(p.email for p in persons)

    for person in persons:
        context['name'] = person.name
        outgoing_email = EmailRequest(
            recipient_email=person.email,
            subject=f"Location Update For {event.name}",
            body=await generate_template(VENUE_REVEAL_TEMPLATE, context)
        )
        await send_email(outgoing_email)
        await asyncio.sleep(2)

    return {"notified": len(persons)}
