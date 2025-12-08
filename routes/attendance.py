from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from decorators import with_db
from enums import PersonStatus
from services.event_ticket import add_ticket_to_db
from services.apple_pass import create_apple_member
from services.google_pass import patch_member_object
from db_models import EventTicket, MemberPass, Person, Event

router = APIRouter(tags=['Attendance'], prefix="/api/attendance")


@router.post("/")
@with_db
async def add_attendance(db: AsyncSession, pass_id: UUID):
    db_pass = await db.get(MemberPass, pass_id)
    if not db_pass:
        db_pass = await db.get(EventTicket, pass_id)
        if not db_pass:
            raise HTTPException(404, "No member pass or ticket found")

    person = await db.get(Person, db_pass.person_id)

    event = await db.scalar(select(Event).where((Event.starts_at < datetime.now()) & (Event.ends_at > datetime.now())))
    # event = await db.get(Event, UUID("21324509-cb82-4a6a-bab1-751d67dad583"))  # TODO remove
    if not event:
        raise HTTPException(404, "Event not found")

    ticket = await db.scalar(select(EventTicket).where(
        (EventTicket.person_id == person.id) & (EventTicket.event_id == event.id)))

    if person.status == PersonStatus.member:
        if not ticket:
            ticket = EventTicket(person_id=person.id, event_id=event.id)
            ticket = await add_ticket_to_db(ticket)
    else:
        if ticket.attended_at:
            raise HTTPException(409, "Used ticket")

    ticket.attended_at = datetime.now()

    db.add(ticket)
    await db.commit()

    if person.status == PersonStatus.member:
        total_attendance = await get_attendance(person.id)
        attendance = str(total_attendance)
        attendance_body = {
            "secondaryLoyaltyPoints": {
                "label": "Events Attended",
                "balance": {
                    "string": attendance,
                },
            }
        }
        await patch_member_object(pass_id, attendance_body)
        await create_apple_member(str(pass_id), f"{person.first_name, person.last_name}", db_pass.serial_number, attendance)

    return person


@router.get("/attendance")
@with_db
async def get_attendance(db: AsyncSession, person_id):
    person = await db.get(Person, person_id)
    if not person:
        raise HTTPException(404, "No such person")

    attendance = await db.scalars(select(EventTicket).where((EventTicket.person_id == person_id) & (EventTicket.attended_at != None)))
    return len(attendance.all())
