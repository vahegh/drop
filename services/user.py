import logging
from sqlalchemy import select
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from enums import PersonStatus
from decorators import with_db
from decorators import verify_user_token
from db_models import Person,  MemberPass
from api_models import PersonUpdate, PersonResponseFull
from services.event_ticket import get_tickets_by_person_id
from services.card_binding import get_card_binding_by_person_id

logger = logging.getLogger(__name__)


@with_db
async def user_info(db: AsyncSession, request: Request):
    person = await verify_user_token(request)
    if person.status == PersonStatus.member:
        member_pass = await db.scalar(select(MemberPass).where(MemberPass.person_id == person.id))
    else:
        member_pass = None

    event_tickets = await get_tickets_by_person_id(person.id)
    attendance = len([e for e in event_tickets if e.attended_at])
    card_bindings = await get_card_binding_by_person_id(person.id)

    response = PersonResponseFull(
        id=person.id,
        first_name=person.first_name,
        last_name=person.last_name,
        full_name=f"{person.first_name} {person.last_name}",
        email=person.email,
        instagram_handle=person.instagram_handle,
        telegram_handle=person.telegram_handle,
        status=person.status,
        avatar_url=person.avatar_url,
        member_pass=member_pass,
        event_tickets=event_tickets,
        events_attended=attendance,
        drive_folder_url=person.drive_folder_url,
        card_bindings=card_bindings
    )

    return response


@with_db
async def modify_user(db: AsyncSession, updated_person: PersonUpdate, request: Request):
    person = await verify_user_token(request)

    if not person:
        raise HTTPException(404, "Person not found")

    if updated_person.email and updated_person.email != person.email:
        existing_email = await db.scalar(select(Person).where(Person.email == updated_person.email))
        if existing_email:
            raise HTTPException(409, "Email already exists")

    for field, value in updated_person.model_dump(exclude_none=True).items():
        setattr(person, field, value)

    await db.commit()
    await db.refresh(person)
    return person
