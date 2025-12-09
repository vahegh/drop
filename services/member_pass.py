from uuid import UUID
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
from consts import GOOGLE_MEMBER_CLASS_ID, TIMEZONE, APP_BASE_URL, MEMBER_PASS_SUBJECT, MEMBER_PASS_TEMPLATE
from services.templating import generate_template
from services.mailing import EmailRequest, send_email
from services.event import get_all_events


@with_db
async def get_next_serial_number(db: AsyncSession) -> int:
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
        member_pass.serial_number = await get_next_serial_number()
        db.add(member_pass)
        await db.commit()
        await db.refresh(member_pass)

    pass_id = str(member_pass.id)
    member_id = str(member_pass.serial_number).zfill(3)
    attendance = str(await get_attendance(member_pass.person_id))

    next_event = await get_next_event()
    person = await db.get(Person, member_pass.person_id)

    google_url = await create_google_member_pass(
        pass_id=pass_id,
        class_id=GOOGLE_MEMBER_CLASS_ID,
        member_id=member_id,
        name=f"{person.first_name} {person.last_name}",
        attendance=attendance
    )

    if next_event:
        venue = await db.get(Venue, next_event.venue_id)
        if not venue:
            raise HTTPException(404, "Venue not found")
        starts_at = next_event.starts_at.astimezone(TIMEZONE).isoformat()
        ends_at = next_event.ends_at.astimezone(TIMEZONE).isoformat()
        event_url = f"{APP_BASE_URL}/event/{next_event.id}"

        apple_url = await create_apple_member(
            pass_id=pass_id,
            name=f"{person.first_name} {person.last_name}",
            member_id=member_id,
            attendance=attendance,
            event_name=next_event.name,
            event_url=event_url,
            venue_name=venue.name,
            lat=venue.latitude,
            long=venue.longitude,
            starts_at=starts_at,
            ends_at=ends_at
        )

    else:
        apple_url = await create_apple_member(
            pass_id=pass_id,
            name=f"{person.first_name} {person.last_name}",
            member_id=member_id,
            attendance=attendance
        )

    await apple_notify_pass_devices(pass_id)

    member_pass.google_pass_url = google_url
    member_pass.apple_pass_url = apple_url

    db.add(person)
    db.add(member_pass)
    await db.commit()
    await db.refresh(member_pass)

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
        "total_events": str(len(await get_all_events()))
    }

    if purchase:
        context["purchase"] = True

    email_template = await generate_template(MEMBER_PASS_TEMPLATE, context=context)

    email_request = EmailRequest(
        recipient_email=person.email,
        subject=MEMBER_PASS_SUBJECT,
        body=email_template
    )
    await send_email(email_request)
