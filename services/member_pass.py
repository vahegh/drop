from uuid import UUID
import logging
from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.event import get_next_event
from decorators import with_db
from enums import PersonStatus
from api_models import MemberCardCreate
from db_models import MemberPass, Person, Venue
from routes.attendance import get_attendance
from services.apple_pass import create_apple_member
from services.google_pass import create_google_member_pass
from services.apple_push_notifications import apple_notify_pass_devices
from consts import APP_BASE_URL, MEMBER_PASS_SUBJECT, MEMBER_PASS_TEMPLATE
from services.templating import generate_template
from services.mailing import EmailRequest, send_email
from services.event import get_all_events


logger = logging.getLogger(__name__)


@with_db
async def get_next_serial_number(db: AsyncSession):
    existing_serials = (await db.scalars(
        select(MemberPass.serial_number).order_by(MemberPass.serial_number)
    )).all()

    if not existing_serials:
        return 1

    for i, serial in enumerate(existing_serials, start=1):
        if serial != i:
            return i

    return existing_serials[-1] + 1


@with_db
async def create_member_pass(db: AsyncSession, member_pass: MemberPass):
    existing = await db.scalar(select(MemberPass).where(MemberPass.person_id == member_pass.person_id))

    if existing:
        member_pass = existing
    else:
        if not member_pass.serial_number:
            member_pass.serial_number = await get_next_serial_number()
        db.add(member_pass)
        await db.commit()
        await db.refresh(member_pass)

    pass_id = str(member_pass.id)
    attendance = str(await get_attendance(member_pass.person_id))

    next_event = await get_next_event()
    person = await db.get(Person, member_pass.person_id)

    full_name = f"{person.first_name} {person.last_name}"

    google_url = await create_google_member_pass(
        name=full_name,
        attendance=attendance,
        member_pass=member_pass
    )

    if next_event:
        venue = await db.get(Venue, next_event.venue_id)
        if not venue:
            raise HTTPException(404, "Venue not found")

        apple_url = await create_apple_member(
            member_pass=member_pass,
            name=full_name,
            attendance=attendance,
            event=next_event,
            venue=venue,
        )

    else:
        apple_url = await create_apple_member(
            member_pass=member_pass,
            name=full_name,
            attendance=attendance,
        )

    await apple_notify_pass_devices(pass_id)

    member_pass.google_pass_url = google_url
    member_pass.apple_pass_url = apple_url

    db.add(member_pass)
    await db.commit()
    await db.refresh(member_pass)

    logger.info(f"Created member pass for {full_name}")

    return member_pass


@with_db
async def get_all_member_passes(db: AsyncSession):
    passes = await db.scalars(select(MemberPass))
    return passes.all()


@with_db
async def get_pass_by_person_id(db: AsyncSession, person_id: UUID):
    member_pass = await db.scalar(select(MemberPass).where(MemberPass.person_id == person_id))
    if not member_pass:
        raise HTTPException(404, "Member pass not found")
    return member_pass


@with_db
async def get_pass(db: AsyncSession, id: UUID):
    member_pass = await db.get(MemberPass, id)
    if not member_pass:
        raise HTTPException(404, "Member pass not found")
    return member_pass


@with_db
async def create_pass(db: AsyncSession, member_pass: MemberCardCreate):
    person = await db.get(Person, member_pass.person_id)
    if not person:
        raise HTTPException(404, "Person not found")
    if person.status is not PersonStatus.member:
        raise HTTPException(400, f"Invalid person status: {person.status}")

    member_pass = await create_member_pass(MemberPass(**member_pass.model_dump(mode='json')))
    await send_member_pass(member_pass)

    return member_pass


@with_db
async def delete_pass(db: AsyncSession, id: UUID):
    db_pass = await db.get(MemberPass, id)
    if not db_pass:
        raise HTTPException(404, "Member pass not found")
    await db.delete(db_pass)
    await db.commit()
    return


@with_db
async def update_apple_member_pass(db: AsyncSession):
    member_passes = await db.scalars(select(MemberPass))
    for t in member_passes.all():
        await create_member_pass(t)
        print(f"Member pass {t.serial_number} updated.")


@with_db
async def send_member_pass(db: AsyncSession, member_pass: MemberPass, purchase=False):
    person = await db.get(Person, member_pass.person_id)

    context = {
        "name": person.first_name,
        "homepage_url": APP_BASE_URL,
        "serial_no": str(member_pass.serial_number).zfill(3),
        "events_attended": str(await get_attendance(person.id)),
        "total_events": str(len(await get_all_events())),
        "purchase": purchase
    }

    email_template = await generate_template(MEMBER_PASS_TEMPLATE, context=context)

    email_request = EmailRequest(
        recipient_email=person.email,
        subject=MEMBER_PASS_SUBJECT,
        body=email_template
    )
    await send_email(email_request)
