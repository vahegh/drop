import logging
import asyncio
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from enums import PersonStatus
from services.templating import generate_template
from services.venue import get_venue_info
from db_models import Event, Venue, Person, EventTicket, MemberPass
from api_models import EventCreate, EventUpdate
from consts import APP_BASE_URL, VENUE_REVEAL_TEMPLATE
from services.google_pass import create_ticket_class, update_member_class
from services.mailing import EmailRequest, send_email
from decorators import with_db
from markdown2 import markdown

logger = logging.getLogger(__name__)


@with_db
async def get_all_events(db: AsyncSession):
    events = await db.scalars(select(Event).order_by(Event.starts_at.desc()))
    return events.all()


@with_db
async def get_next_event(db: AsyncSession):
    event = await db.scalar(select(Event).where(Event.ends_at >= datetime.now(timezone.utc)).where(Event.shared == True).limit(1))
    return event


@with_db
async def get_event_info(db: AsyncSession, id: UUID):
    return await db.get(Event, id)


@with_db
async def create_event(db: AsyncSession, event: EventCreate):
    venue = await get_venue_info(event.venue_id)
    event = Event(**event.model_dump())

    db.add(event)
    await db.commit()
    await db.refresh(event)

    await create_ticket_class(event=event, venue=venue)
    return event


@with_db
async def update_event(db: AsyncSession, id: UUID, request: EventUpdate):
    event = await db.get(Event, id)
    if not event:
        raise HTTPException(404, "Event not found")

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    venue = await db.get(Venue, event.venue_id)

    await update_member_class(event=event, venue=venue)
    await create_ticket_class(event=event, venue=venue)

    await db.commit()
    await db.refresh(event)
    return event


@with_db
async def delete_event(db: AsyncSession, id: UUID):
    event = await db.get(Event, id)
    if not event:
        raise HTTPException(404, "Event not found")
    await db.delete(event)
    await db.commit()
    return


@with_db
async def early_bird_end(db: AsyncSession, event_id: UUID):
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(404, "Event not found")

    starts_at_local = event.starts_at.astimezone()
    ends_at_local = event.ends_at.astimezone()
    early_bird_tier = next((t for t in event.tiers if t.available_until and not t.required_person_status), None)
    ga_tier = next((t for t in event.tiers if not t.required_person_status and not t.available_until), None)
    context = {
        "event_name": event.name,
        "event_day_of_week": starts_at_local.strftime("%A"),
        "early_bird_price": f"{early_bird_tier.price} AMD" if early_bird_tier else "-",
        "standard_price": f"{ga_tier.price} AMD" if ga_tier else "-",
        "event_url": f"{APP_BASE_URL}/event/{event.id}",
        "event_date": starts_at_local.strftime("%A %d %B"),
        "start_time": starts_at_local.strftime("%H:%M"),
        "end_time": ends_at_local.strftime("%H:%M"),
        "unsubscribe_url": f"{APP_BASE_URL}/unsubscribe",
        "preheader_text": "Your review has started. You'll be updated shortly."
    }

    persons = (await db.scalars(select(Person)
                                .outerjoin(EventTicket, (EventTicket.person_id == Person.id) & (EventTicket.event_id == event_id))
                                .where(Person.status == PersonStatus.verified)
                                .where(EventTicket.id.is_(None)))).all()

    for p in persons:
        context['name'] = p.first_name
        outgoing_email = EmailRequest(
            recipient_email=p.email,
            subject=f"Early Bird - {event.name}",
            body=await generate_template("early_bird_reminder.html", context)
        )
        await send_email(outgoing_email)


@with_db
async def event_announcement(db: AsyncSession, event_id: UUID):
    event = await get_next_event()

    if not event:
        raise HTTPException(404, "No upcoming event")

    all_verified_without_tickets = (
        await db.scalars(
            select(Person)
            .where(Person.status.not_in([PersonStatus.pending, PersonStatus.rejected]))
            .outerjoin(EventTicket, (EventTicket.person_id == Person.id) & (EventTicket.event_id == event_id))
            .where(EventTicket.id.is_(None))
        )
    ).all()

    starts_at_local = event.starts_at.astimezone()
    ends_at_local = event.ends_at.astimezone()

    early_bird_tier = next((t for t in event.tiers if t.available_until and not t.required_person_status), None)
    ga_tier = next((t for t in event.tiers if not t.required_person_status and not t.available_until), None)
    member_tier = next((t for t in event.tiers if t.required_person_status == PersonStatus.member), None)
    context = {
        "event_name": event.name,
        "description": markdown(event.description),
        "event_date": event.starts_at.astimezone().strftime("%A, %d %B"),
        "start_time": starts_at_local.strftime("%H:%M"),
        "end_time": ends_at_local.strftime("%H:%M"),
        "early_bird_date": early_bird_tier.available_until.astimezone().strftime("%d.%m") if early_bird_tier else "-",
        "early_bird_price": f"{early_bird_tier.price} AMD" if early_bird_tier else "-",
        "standard_price": f"{ga_tier.price} AMD" if ga_tier else "-",
        "member_price": f"{member_tier.price} AMD" if member_tier else "-",
        "event_url": f"{APP_BASE_URL}/event/{event.id}?utm_source=email&utm_medium=marketing&utm_campaign=announcement_{event.id}",
    }

    for p in all_verified_without_tickets:
        context["unsubscribe_url"] = f"{APP_BASE_URL}/unsubscribe?email={p.email}"
        outgoing_email = EmailRequest(
            recipient_email=p.email,
            subject=f"🪩 {event.starts_at.astimezone().strftime("%A %d %B")} | {event.name}",
            body=await generate_template("event_announcement.html", context)
        )
        await send_email(outgoing_email)


@with_db
async def event_notify(db: AsyncSession):
    event = await get_next_event()

    if not event:
        raise HTTPException(404, "No upcoming event")

    all_verified_without_tickets = (
        await db.scalars(
            select(Person)
            .where(Person.status.not_in([PersonStatus.pending, PersonStatus.rejected]))
            .outerjoin(EventTicket, (EventTicket.person_id == Person.id) & (EventTicket.event_id == event.id))
            .where(EventTicket.id.is_(None))
        )
    ).all()

    context = {
        "event_name": event.name,
        "description": markdown(event.description),
        "buy_ticket_url": f"{APP_BASE_URL}/buy-ticket?event_id={event.id}&utm_source=email&utm_medium=marketing&utm_campaign=2_days_left_{event.id}"
    }

    for p in all_verified_without_tickets:
        context['name'] = p.first_name
        outgoing_email = EmailRequest(
            recipient_email=p.email,
            subject=f"This Saturday - {event.name}",
            body=await generate_template("purchase_reminder.html", context),
        )

        await send_email(outgoing_email)


@with_db
async def venue_reveal(db: AsyncSession):
    event = await get_next_event()
    if not event:
        raise HTTPException(404, "No such event")

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

    # persons = (await db.scalars(select(Person).where(Person.id == 'c8571072-a0b6-4e27-b646-0090070fa74c'))).all()

    for person in persons:
        context['name'] = person.first_name
        outgoing_email = EmailRequest(
            recipient_email=person.email,
            subject=f"Location Update For {event.name}",
            body=await generate_template(VENUE_REVEAL_TEMPLATE, context)
        )
        await send_email(outgoing_email)
        # await asyncio.sleep(1)

    return {"notified": len(persons)}
