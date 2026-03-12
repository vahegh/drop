from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Response
from decorators import with_db
from db_models import Person, RefreshToken
from enums import PersonStatus, PaymentStatus
from services.event import get_next_event
from services.telegram import notify_application
from services.templating import generate_template
from services.mailing import EmailRequest, send_email
from services.payment import get_payment, refund_payment
from services.event_ticket import EventTicket, create_event_ticket, send_event_ticket
from services.payment_intent import get_payment_intent, get_confirmed_payment_intent, delete_payment_intent
from api_models import PersonCreate, PersonUpdate
from consts import (APP_BASE_URL, APPLICATION_SUBMITTED_TEMPLATE, APPROVED_TEMPLATE,
                    REJECTED_TEMPLATE, APPLICATION_SUBMITTED_SUBJECT,
                    STATUS_CHANGE_SUBJECT)
from routes.attendance import get_attendance


@with_db
async def get_person_by_email(db: AsyncSession, email: str):
    return await db.scalar(select(Person).where(func.lower(Person.email) == email.lower()))


@with_db
async def get_all_person_stats(db: AsyncSession):
    result = await db.execute(
        select(Person.status, func.count(Person.id).label('count'))
        .where(Person.status.in_([PersonStatus.verified, PersonStatus.member]))
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
    await db.refresh(new_person)

    if person.referer_id:
        referer = await get_person(person.referer_id)
        ref_attendance = await get_attendance(referer.id)

        if referer.status == PersonStatus.member or ref_attendance >= 2:
            new_person = await update_person(new_person.id, PersonUpdate(status=PersonStatus.verified))

    else:
        context = {"name": person.first_name}

        template = await generate_template(APPLICATION_SUBMITTED_TEMPLATE, context)

        email_request = EmailRequest(
            recipient_email=new_person.email,
            subject=APPLICATION_SUBMITTED_SUBJECT,
            body=template
        )
        await send_email(email_request)

    await notify_application(new_person)

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

    next_event = await get_next_event()

    match updated_person.status:
        case PersonStatus.rejected:
            if person.status == PersonStatus.pending:
                if next_event:
                    intent = await get_confirmed_payment_intent(person.id, next_event.id)
                    if intent:
                        existing_payment = await get_payment(intent.order_id)
                        await refund_payment(existing_payment)
                        context["refunded"] = True
                        await delete_payment_intent(intent.order_id, person.id)

                template = await generate_template(REJECTED_TEMPLATE, context)
                email_request = EmailRequest(
                    recipient_email=person.email,
                    subject=STATUS_CHANGE_SUBJECT,
                    body=template
                )

        case PersonStatus.verified:
            if person.status == PersonStatus.pending:
                ticket_sent = False

                if next_event:
                    intent = await get_confirmed_payment_intent(person.id, next_event.id)
                    if intent:
                        existing_payment = await get_payment(intent.order_id)
                        event_ticket = EventTicket(
                            person_id=person.id,
                            event_id=existing_payment.event_id,
                            payment_order_id=existing_payment.order_id
                        )
                        await create_event_ticket(event_ticket)
                        await send_event_ticket(event_ticket)
                        await delete_payment_intent(intent.order_id, person.id)
                        ticket_sent = True

                if not ticket_sent:
                    if next_event:
                        context["event_name"] = next_event.name
                        context["event_url"] = f"{APP_BASE_URL}/buy-ticket?event_id={next_event.id}&utm_source=email&utm_medium=transactional&utm_campaign=account_approved&utm_content=buy_ticket_cta"

                    template = await generate_template(APPROVED_TEMPLATE, context)
                    email_request = EmailRequest(
                        recipient_email=person.email,
                        subject=STATUS_CHANGE_SUBJECT,
                        body=template
                    )

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
