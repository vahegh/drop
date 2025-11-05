from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from routes.event import get_next_event
from db_models import MemberPass, Person, Venue
from consts import GOOGLE_MEMBER_CLASS_ID, TIMEZONE, APP_BASE_URL
from routes.attendance import get_attendance
from services.apple_pass import create_apple_member
from services.google_pass import create_google_member_pass
from services.apple_push_notifications import apple_notify_pass_devices
from services.drive import drive_service
from db import with_db


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

    if next_event:
        venue = await db.get(Venue, next_event.venue_id)
        if not venue:
            raise HTTPException(404, "Venue not found")
        starts_at = next_event.starts_at.astimezone(TIMEZONE).isoformat()
        ends_at = next_event.ends_at.astimezone(TIMEZONE).isoformat()
        event_url = f"{APP_BASE_URL}/event/{next_event.id}"

        google_url = await create_google_member_pass(pass_id, GOOGLE_MEMBER_CLASS_ID, member_id, person.name, attendance)
        apple_url = await create_apple_member(pass_id,
                                              person.name,
                                              member_id,
                                              attendance,
                                              next_event.name,
                                              event_url,
                                              venue.name,
                                              venue.latitude,
                                              venue.longitude,
                                              starts_at,
                                              ends_at)
    else:
        google_url = await create_google_member_pass(pass_id, GOOGLE_MEMBER_CLASS_ID, member_id, person.name, attendance)
        apple_url = await create_apple_member(pass_id, person.name, member_id, attendance)

    await apple_notify_pass_devices(pass_id)

    member_pass.google_pass_url = google_url
    member_pass.apple_pass_url = apple_url

    person.drive_folder_url = await drive_service.create_and_share_folder(person)

    db.add(person)
    db.add(member_pass)
    await db.commit()
    await db.refresh(member_pass)

    return member_pass, existing
