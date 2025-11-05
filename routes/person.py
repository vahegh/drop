from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Response
from db import with_db
from db_models import Person, MemberPass, RefreshToken
from enums import PersonStatus
from routes.event import get_next_event
from services.auth import create_jwt
from services.auth_validation import validate_google_token
from services.send_pass import send_member_pass
from services.telegram import notify_application
from services.templating import generate_template
from services.member_pass import create_member_pass
from services.mailing import EmailRequest, send_email
from api_models import PersonCreate, PersonResponse, PersonUpdate
from consts import (APP_BASE_URL, APPLICATION_SUBMITTED_TEMPLATE, APPROVED_TEMPLATE,
                    REJECTED_TEMPLATE, APPLICATION_SUBMITTED_SUBJECT,
                    STATUS_CHANGE_SUBJECT)

router = APIRouter(tags=["Person"], prefix="/api/person")


@router.get("/all", response_model=list[PersonResponse], dependencies=[Depends(validate_google_token)])
@with_db
async def get_all_persons(db: AsyncSession):
    persons = await db.scalars(select(Person))
    return persons.all()


@router.get("/{id}", response_model=PersonResponse, dependencies=[Depends(validate_google_token)])
@with_db
async def get_person(db: AsyncSession, id: UUID):
    existing_person = await db.get(Person, id)
    if not existing_person:
        raise HTTPException(404, "Person not found")
    return existing_person


@router.post("/", response_model=PersonResponse)
@with_db
async def create_person(db: AsyncSession, person: PersonCreate):
    existing_email = await db.scalar(select(Person).where(Person.email == person.email))
    if existing_email:
        raise HTTPException(409, "Email already exists")

    new_person = Person(**person.model_dump())
    db.add(new_person)
    await db.commit()
    await notify_application(new_person)

    context = {"name": person.name}
    template = await generate_template(APPLICATION_SUBMITTED_TEMPLATE, context)

    email_request = EmailRequest(
        recipient_email=new_person.email,
        subject=APPLICATION_SUBMITTED_SUBJECT,
        body=template
    )

    await send_email(email_request)
    return new_person


@router.put("/{id}", response_model=PersonResponse, dependencies=[Depends(validate_google_token)])
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
    context = {"name": person.name}

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

        case PersonStatus.approved:
            next_event = await get_next_event()

            if next_event:
                token = await create_jwt(person.email, str(next_event.id), expires_in=1440)
                context["event_name"] = next_event.name
                context["payment_link"] = f"{APP_BASE_URL}/buy-ticket?token={token}"

            template = await generate_template(APPROVED_TEMPLATE, context)

            email_request = EmailRequest(
                recipient_email=person.email,
                subject=STATUS_CHANGE_SUBJECT,
                body=template
            )

        case PersonStatus.member:
            member_pass = MemberPass(person_id=person.id)
            member_pass, _ = await create_member_pass(member_pass)
            await send_member_pass(member_pass, resend=False)

    if email_request:
        await send_email(email_request)

    for field, value in updated_person.model_dump().items():
        if value is not None:
            setattr(person, field, value)
    await db.commit()
    await db.refresh(person)
    return person


@router.delete("/{id}", dependencies=[Depends(validate_google_token)])
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


@router.get("/email/{email}", response_model=PersonResponse, dependencies=[Depends(validate_google_token)])
@with_db
async def get_person_by_email(db: AsyncSession, email: str):
    existing_person = await db.scalar(select(Person).where(func.lower(Person.email) == email.lower()))
    if not existing_person:
        raise HTTPException(404, "Person not found")
    return existing_person
