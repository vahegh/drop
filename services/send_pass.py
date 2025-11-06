from datetime import timedelta, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from enums import PersonStatus
from consts import APP_BASE_URL
from services.templating import generate_template
from services.mailing import EmailRequest, send_email
from routes.attendance import get_attendance
from routes.event import get_all_events
from db_models import Person, Event, MemberPass, EventTicket, Venue
from consts import (APP_BASE_URL, MEMBER_PASS_TEMPLATE, EVENT_TICKET_TEMPLATE,
                    MEMBER_PASS_SUBJECT, EVENT_TICKET_SUBJECT, TIMEZONE, MAGIC_LINK_SUBJECT, MAGIC_LINK_TEMPLATE)
from db import with_db


async def send_magic_link(person: Person, event_name: str, link: str):
    context = {
        "name": person.name,
        "event_name": event_name,
        "payment_link": link
    }
    email_template = await generate_template(MAGIC_LINK_TEMPLATE, context=context)
    email_request = EmailRequest(
        recipient_email=person.email,
        subject=MAGIC_LINK_SUBJECT,
        body=email_template
    )
    await send_email(email_request)


@with_db
async def send_member_pass(db: AsyncSession, member_pass: MemberPass, purchase=False, resend=False):
    person = await db.get(Person, member_pass.person_id)

    context = {
        "name": person.name,
        "pass_page": f"{APP_BASE_URL}/pass/{person.id}",
        "serial_no": str(member_pass.serial_number).zfill(3),
        "events_attended": str(await get_attendance(person.id)),
        "total_events": str(len(await get_all_events()))
    }

    if purchase:
        context["purchase"] = True
    if resend:
        context["resend"] = True

    email_template = await generate_template(MEMBER_PASS_TEMPLATE, context=context)

    email_request = EmailRequest(
        recipient_email=person.email,
        subject=MEMBER_PASS_SUBJECT,
        body=email_template
    )
    await send_email(email_request)


@with_db
async def send_event_ticket(db: AsyncSession, event_ticket: EventTicket, resend=False):
    person = await db.get(Person, event_ticket.person_id)
    event = await db.get(Event, event_ticket.event_id)

    event_datetime_local = event.starts_at.astimezone(TIMEZONE)
    context = {
        "name": person.name,
        "event_name": event.name,
        "pass_page": f"{APP_BASE_URL}/pass/{person.id}",
        "event_date": event_datetime_local.strftime("%A, %d %B"),
        "event_time": event_datetime_local.strftime("%H:%M"),
        "is_verified": True if person.status == PersonStatus.verified else False
    }
    if resend:
        context["resend"] = True

    subject = EVENT_TICKET_SUBJECT.format(event_name=event.name)

    if datetime.now(timezone.utc) + timedelta(1) > event.starts_at:
        venue = await db.get(Venue, event.venue_id)
        context['location'] = f"{venue.name}, {venue.address}"
        context['google_maps_link'] = venue.google_maps_link
        context['yandex_maps_link'] = venue.yandex_maps_link

    template = await generate_template(template_name=EVENT_TICKET_TEMPLATE, context=context)

    email_request = EmailRequest(
        recipient_email=person.email,
        subject=subject,
        body=template
    )

    await send_email(email_request)
