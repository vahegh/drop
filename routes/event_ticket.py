import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Depends
from db import with_db
from enums import PersonStatus
from services.send_pass import send_event_ticket
from db_models import EventTicket, Person, Event
from api_models import EventTicketCreate, EventTicketResponse
from services.event_ticket import create_event_ticket, add_ticket_to_db

router = APIRouter(tags=['Event Ticket'], prefix="/api/event-ticket")
logger = logging.getLogger(__name__)


@router.get("/all", response_model=list[EventTicketResponse])
@with_db
async def get_all_tickets(db: AsyncSession, event_id: str = None):
    if event_id:
        tickets = await db.scalars(select(EventTicket).where(EventTicket.event_id == event_id))
    else:
        tickets = await db.scalars(select(EventTicket))
    return tickets.all()


@router.get("/person/{person_id}", response_model=list[EventTicketResponse])
@with_db
async def get_tickets_by_person_id(db: AsyncSession, person_id: UUID, event_id: UUID = None):
    if event_id:
        tickets = await db.scalars(select(EventTicket).where((EventTicket.person_id == person_id) & (EventTicket.event_id == event_id)))
    else:
        tickets = await db.scalars(select(EventTicket).where(EventTicket.person_id == person_id))
    return tickets.all()


@router.get("/{id}", response_model=EventTicketResponse)
@with_db
async def get_ticket(db: AsyncSession, id: UUID):
    event_ticket = await db.get(EventTicket, id)
    if not event_ticket:
        raise HTTPException(404, "Event ticket not found")
    return event_ticket


@router.post("/", response_model=EventTicketResponse)
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


@router.delete("/{id}")
@with_db
async def delete_event_ticket(db: AsyncSession, id: UUID):
    db_ticket = await db.get(EventTicket, id)
    if not db_ticket:
        raise HTTPException(404, "Event not found")
    await db.delete(db_ticket)
    await db.commit()
    return


@router.post("/update-apple-ticket-info")
@with_db
async def update_apple_ticket_info(db: AsyncSession, event_id: UUID):
    tickets = await db.scalars(select(EventTicket).where(EventTicket.event_id == event_id))
    for t in tickets.all():
        person = await db.get(Person, t.person_id)
        if person.status == PersonStatus.member:
            print("member, continuing")
            continue
        await create_event_ticket(t)
        print(f"ticket updated for {person.name}")
