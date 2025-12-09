from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Response
from decorators import with_db
from db_models import Person, MemberPass, RefreshToken
from enums import PersonStatus
from services.event import get_next_event
from services.auth import create_jwt
from services.telegram import notify_application
from services.templating import generate_template
from services.member_pass import create_member_pass, send_member_pass
from services.mailing import EmailRequest, send_email
from api_models import PersonCreate, PersonUpdate
from consts import (APP_BASE_URL, APPLICATION_SUBMITTED_TEMPLATE, APPROVED_TEMPLATE,
                    REJECTED_TEMPLATE, APPLICATION_SUBMITTED_SUBJECT,
                    STATUS_CHANGE_SUBJECT)


@with_db
async def get_person_by_email(db: AsyncSession, email: str):
    return await db.scalar(select(Person).where(func.lower(Person.email) == email.lower()))


@with_db
async def get_all_person_stats(db: AsyncSession):
    result = await db.execute(
        select(Person.status, func.count(Person.id).label('count'))
        .group_by(Person.status)
    )

    stats = {row[0]: row[1] for row in result.all()}

    return stats


@with_db
async def get_all_persons(db: AsyncSession):
    persons = await db.scalars(select(Person))
    return persons.all()


@with_db
async def get_person(db: AsyncSession, id: UUID):
    existing_person = await db.get(Person, id)
    if not existing_person:
        raise HTTPException(404, "Person not found")
    return existing_person


@with_db
async def create_person(db: AsyncSession, person: PersonCreate):
    existing_email = await db.scalar(select(Person).where(Person.email == person.email))
    if existing_email:
        raise HTTPException(409, "Email already exists")

    new_person = Person(**person.model_dump())
    db.add(new_person)
    await db.commit()
    await notify_application(new_person)

    context = {"name": person.first_name}
    template = await generate_template(APPLICATION_SUBMITTED_TEMPLATE, context)

    email_request = EmailRequest(
        recipient_email=new_person.email,
        subject=APPLICATION_SUBMITTED_SUBJECT,
        body=template
    )

    await send_email(email_request)
    return new_person


@with_db
async def update_person(db: AsyncSession, id: UUID, updated_person: PersonUpdate):
    person = await db.get(Person, id)
    if not person:
        raise HTTPException(404, "Person not found")
    if updated_person.email and updated_person.email != person.email:
        if updated_person.status and updated_person.status != person.status:
            raise HTTPException(
                400, "Can't update email and status at the same time")
        existing_email = await db.scalar(select(Person).where(Person.email == updated_person.email))
        if existing_email:
            raise HTTPException(409, "Email already exists")

    email_request = None
    context = {"name": person.first_name}

    match updated_person.status:
        case None:
            pass

        case PersonStatus.rejected:
            template = await generate_template(REJECTED_TEMPLATE, context)
            email_request = EmailRequest(
                recipient_email=person.email,
                subject=STATUS_CHANGE_SUBJECT,
                body=template
            )

        case PersonStatus.verified:
            next_event = await get_next_event()

            if next_event:
                context["event_name"] = next_event.name
                context["event_url"] = f"{APP_BASE_URL}/buy-ticket?event_id={next_event.id}"

            template = await generate_template(APPROVED_TEMPLATE, context)

            email_request = EmailRequest(
                recipient_email=person.email,
                subject=STATUS_CHANGE_SUBJECT,
                body=template
            )

        case PersonStatus.member:
            member_pass = MemberPass(person_id=person.id)
            member_pass = await create_member_pass(member_pass)
            await send_member_pass(member_pass)

    if email_request:
        await send_email(email_request)

    for field, value in updated_person.model_dump(exclude_unset=True).items():
        setattr(person, field, value)
    await db.commit()
    await db.refresh(person)
    return person


@with_db
async def delete_person(db: AsyncSession, id: UUID):
    existing_person = await db.get(Person, id)
    if not existing_person:
        raise HTTPException(404, "Person not found")
    refresh_tokens = await db.scalars(select(RefreshToken).where(RefreshToken.person_id == existing_person.id))
    for token in refresh_tokens.all():
        await db.delete(token)
    await db.commit()
    await db.delete(existing_person)
    await db.commit()
    return Response("Person deleted")
