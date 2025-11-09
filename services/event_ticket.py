import logging
from uuid import UUID
from datetime import timedelta, datetime, timezone
from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from consts import TIMEZONE, APP_BASE_URL, EVENT_TICKET_SUBJECT, EVENT_TICKET_TEMPLATE
from enums import PersonStatus
from decorators import with_db
from api_models import EventTicketCreate
from db_models import EventTicket, Person, Event, Venue
from services.apple_pass import create_apple_ticket
from services.google_pass import create_google_ticket
from services.apple_push_notifications import apple_notify_pass_devices
from services.templating import generate_template
from services.mailing import EmailRequest, send_email

logger = logging.getLogger(__name__)


@with_db
async def add_ticket_to_db(db: AsyncSession, ticket: EventTicket):
    existing = await db.scalar(select(EventTicket)
                               .where((EventTicket.person_id == ticket.person_id) & (EventTicket.event_id == ticket.event_id)))
    if existing:
        return existing
    else:
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)

    return ticket


@with_db
async def create_event_ticket(db: AsyncSession, ticket: EventTicket):
    ticket = await add_ticket_to_db(ticket)

    person = await db.get(Person, ticket.person_id)
    event = await db.get(Event, ticket.event_id)
    venue = await db.get(Venue, event.venue_id)

    pass_id = str(ticket.id)
    starts_at = event.starts_at.astimezone(TIMEZONE).isoformat()
    ends_at = event.ends_at.astimezone(TIMEZONE).isoformat()
    event_url = f"{APP_BASE_URL}/event/{event.id}"

    google_url = await create_google_ticket(pass_id, event.id, f"{person.first_name} {person.last_name}")
    apple_url = await create_apple_ticket(pass_id,
                                          f"{person.first_name} {person.last_name}",
                                          event.name,
                                          event_url,
                                          venue.name,
                                          venue.latitude,
                                          venue.longitude,
                                          starts_at,
                                          ends_at)
    ticket.google_pass_url = google_url
    ticket.apple_pass_url = apple_url
    await apple_notify_pass_devices(pass_id)

    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    return ticket


@with_db
async def get_all_tickets(db: AsyncSession, event_id: str = None):
    if event_id:
        tickets = await db.scalars(select(EventTicket).where(EventTicket.event_id == event_id))
    else:
        tickets = await db.scalars(select(EventTicket))
    return tickets.all()


@with_db
async def get_tickets_by_person_id(db: AsyncSession, person_id: UUID, event_id: UUID = None):
    query = select(EventTicket).where(EventTicket.person_id == person_id)

    if event_id:
        query = query.where(EventTicket.event_id == event_id)

    query = query.order_by(EventTicket.created_at.desc())

    result = await db.scalars(query)
    return result.all()


@with_db
async def get_ticket(db: AsyncSession, id: UUID):
    event_ticket = await db.get(EventTicket, id)
    if not event_ticket:
        raise HTTPException(404, "Event ticket not found")
    return event_ticket


@with_db
async def create_ticket(db: AsyncSession, request: EventTicketCreate):
    person = await db.get(Person, request.person_id)
    if not person:
        raise HTTPException(404, "Person not found")

    if not await db.get(Event, request.event_id):
        raise HTTPException(404, "Event not found")

    if person.status in (PersonStatus.pending, PersonStatus.rejected):
        raise HTTPException(400, f"Invalid person status: {person.status}")

    ticket = EventTicket(**request.model_dump())

    if person.status == PersonStatus.member:
        ticket = await add_ticket_to_db(ticket)
    else:
        ticket = await create_event_ticket(ticket)
        await send_event_ticket(ticket)

    return ticket


@with_db
async def delete_event_ticket(db: AsyncSession, id: UUID):
    db_ticket = await db.get(EventTicket, id)
    if not db_ticket:
        raise HTTPException(404, "Event not found")
    await db.delete(db_ticket)
    await db.commit()
    return


@with_db
async def update_apple_ticket_info(db: AsyncSession, event_id: UUID):
    tickets = await db.scalars(select(EventTicket).where(EventTicket.event_id == event_id))
    for t in tickets.all():
        person = await db.get(Person, t.person_id)
        if person.status == PersonStatus.member:
            print("member, continuing")
            continue
        await create_event_ticket(t)
        print(f"ticket updated for {f"{person.first_name} {person.last_name}"}")


@with_db
async def send_event_ticket(db: AsyncSession, event_ticket: EventTicket):
    person = await db.get(Person, event_ticket.person_id)
    event = await db.get(Event, event_ticket.event_id)

    starts_at_local = event.starts_at.astimezone(TIMEZONE)
    ends_at_local = event.starts_at.astimezone(TIMEZONE)
    context = {
        "name": person.first_name,
        "event_name": event.name,
        "homepage_url": APP_BASE_URL,
        "event_date": starts_at_local.strftime("%A, %d %B"),
        "start_time": starts_at_local.strftime("%H:%M"),
        "end_time": ends_at_local.strftime("%H:%M"),
    }

    subject = EVENT_TICKET_SUBJECT.format(event_name=event.name)

    if datetime.now(timezone.utc) + timedelta(1) > event.starts_at:
        venue = await db.get(Venue, event.venue_id)
        context['location'] = f"{venue.name}, {venue.address}"
        context['google_maps_link'] = venue.google_maps_link
        context['yandex_maps_link'] = venue.yandex_maps_link

    template = await generate_template(template_name=EVENT_TICKET_TEMPLATE, context=context)

    email_request = EmailRequest(
        recipient_email=person.email,
        subject=subject,
        body=template
    )

    await send_email(email_request)
