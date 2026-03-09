from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decorators import with_db
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db_models import Person, MemberPass, EventTicket, CardBinding
from enums import PersonStatus
from api_models import PersonCreate, PersonUpdate, PersonResponseFull, MemberCardResponse, EventTicketResponse, CardBindingResponse
from services.person import update_person

router = APIRouter(tags=["Admin People"], prefix="/people")


class StatusUpdate(BaseModel):
    status: PersonStatus


@router.get("")
async def list_people(status: Optional[str] = None):
    return await _get_people(status)


@router.post("")
async def create_person(body: PersonCreate):
    return await _create_person(body)


@with_db
async def _create_person(db: AsyncSession, body: PersonCreate):
    person = Person(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        instagram_handle=body.instagram_handle,
        telegram_handle=body.telegram_handle,
        avatar_url=body.avatar_url,
        referer_id=body.referer_id,
    )
    db.add(person)
    await db.commit()
    await db.refresh(person)
    return person


@with_db
async def _get_people(db: AsyncSession, status: Optional[str]):
    q = select(Person)
    if status:
        q = q.where(Person.status == PersonStatus(status))
    q = q.order_by(Person.status, Person.first_name)
    result = await db.scalars(q)
    return result.all()


@router.get("/{id}")
async def person_detail(id: UUID):
    return await _get_person_detail(id)


@with_db
async def _get_person_detail(db: AsyncSession, id: UUID):
    person = await db.get(Person, id)
    if not person:
        raise HTTPException(404, "Person not found")

    member_pass = await db.scalar(select(MemberPass).where(MemberPass.person_id == id))

    tickets_result = await db.scalars(select(EventTicket).where(EventTicket.person_id == id))
    tickets = tickets_result.all()
    events_attended = sum(1 for t in tickets if t.attended_at)

    referral_count = await db.scalar(
        select(func.count(Person.id)).where(Person.referer_id == id)
    ) or 0

    bindings_result = await db.scalars(select(CardBinding).where(CardBinding.person_id == id))
    bindings = bindings_result.all()

    return PersonResponseFull(
        id=person.id,
        first_name=person.first_name,
        last_name=person.last_name,
        full_name=f"{person.first_name} {person.last_name}",
        email=person.email,
        instagram_handle=person.instagram_handle or '',
        telegram_handle=person.telegram_handle,
        status=person.status,
        avatar_url=person.avatar_url,
        drive_folder_url=person.drive_folder_url,
        member_pass=MemberCardResponse.model_validate(member_pass) if member_pass else None,
        event_tickets=[EventTicketResponse.model_validate(t) for t in tickets],
        events_attended=events_attended,
        referral_count=referral_count,
        card_bindings=[CardBindingResponse.model_validate(b) for b in bindings],
    )


@router.patch("/{id}/status")
async def update_person_status(id: UUID, body: StatusUpdate):
    return await update_person(id, PersonUpdate(status=body.status))
