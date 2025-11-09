from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from consts import TIMEZONE, APP_BASE_URL
from services.apple_pass import create_apple_ticket
from services.google_pass import create_google_ticket
from db_models import EventTicket, Person, Event, Venue
from services.apple_push_notifications import apple_notify_pass_devices
from decorators import with_db


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

    google_url = await create_google_ticket(pass_id, event.id, person.name)
    apple_url = await create_apple_ticket(pass_id,
                                          person.name,
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
