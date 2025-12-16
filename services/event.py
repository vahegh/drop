import logging
from uuid import UUID
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from enums import PersonStatus
from services.templating import generate_template
from services.venue import get_venue_info
from db_models import Event, Venue, Person, EventTicket
from api_models import EventCreate, EventUpdate
from consts import APP_BASE_URL
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
    event = await db.scalar(select(Event).where(Event.ends_at >= date.today()).limit(1))
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

    venue = await db.get(Venue, event.venue_id)
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

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
    context = {
        "event_name": event.name,
        "event_day_of_week": starts_at_local.strftime("%A"),
        "early_bird_price": f"{event.early_bird_price} AMD",
        "standard_price": f"{event.general_admission_price} AMD",
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
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(404, "No such event")

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

    context = {
        "event_name": event.name,
        "description": markdown(event.description),
        "event_date": event.starts_at.astimezone().strftime("%A, %d %B"),
        "start_time": starts_at_local.strftime("%H:%M"),
        "end_time": ends_at_local.strftime("%H:%M"),
        "early_bird_date": event.early_bird_date.astimezone().strftime("%d.%m"),
        "early_bird_price": f"{event.early_bird_price} AMD",
        "standard_price": f"{event.general_admission_price} AMD",
        "member_price": f"{event.member_ticket_price} AMD",
        "event_url": f"{APP_BASE_URL}/event/{event.id}",
    }

    for p in all_verified_without_tickets:
        context["unsubscribe_url"] = f"{APP_BASE_URL}/unsubscribe?email={p.email}"
        outgoing_email = EmailRequest(
            recipient_email=p.email,
            subject=f"🪩 {event.starts_at.astimezone().strftime("%A %d %B")} | {event.name}",
            body=await generate_template("event_announcement.html", context),
            transactional=False
        )
        await send_email(outgoing_email)


@with_db
async def event_notify(db: AsyncSession, event_id: UUID):
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(404, "No such event")
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

    context = {
        "event_name": event.name,
        "description": markdown(event.description),
        "event_date": event.starts_at.astimezone().strftime("%A, %d %B"),
        "start_time": starts_at_local.strftime("%H:%M"),
        "end_time": ends_at_local.strftime("%H:%M"),
        "standard_price": f"{event.general_admission_price} AMD",
        "member_price": f"{event.member_ticket_price} AMD",
        "event_url": f"{APP_BASE_URL}/event/{event.id}"
    }

    for p in all_verified_without_tickets:
        context['name'] = p.first_name
        outgoing_email = EmailRequest(
            recipient_email=p.email,
            subject=f"Tomorrow - {event.name}",
            body=await generate_template("purchase_reminder.html", context)
        )

        await send_email(outgoing_email)
