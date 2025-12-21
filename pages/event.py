from datetime import timezone, datetime
from nicegui import ui
from fastapi import HTTPException, Request
from uuid import UUID
from frame import frame
from helpers import get_album_urls, gtag_event, fbq_event, share_event
from components import (event_datetime_card, event_card, image_carousel, primary_button,
                        ticket_card, section, location_card, outline_button)
from services.event import get_event_info
from dependencies import Depends, logged_in
from api_models import PersonResponseFull
from enums import PersonStatus

PHOTO_STORAGE_DIR = "photos"


@ui.page('/drop-5')
async def drop_5():
    ui.navigate.to("/event/d350a039-2316-41b4-9dfd-5d9c1e715d71")
    return


@ui.page('/event/{event_id}', response_timeout=10)
async def event_page(event_id: UUID, request: Request, logged_in=Depends(logged_in)):
    event = await get_event_info(event_id)
    if not event:
        raise HTTPException(404)

    if logged_in:
        person: PersonResponseFull = ui.context.client.request.state.person

    ui.page_title(f'{event.name} | Drop Dead Disco')

    async with frame():
        event_passed = event.ends_at < datetime.now(timezone.utc)

        with ui.grid().classes('flex w-full justify-center p-0 gap-2'):
            with section():
                event_card(event)
                # outline_button("Share with a friend").props(
                #     'icon-right="send"').on_click(lambda: share_event(event, request.headers.get('user-agent', '').lower()))
                ui.markdown(f"""
## {event.name}  
**Kentron, Yerevan**  
{event.starts_at.astimezone().strftime("%d %B | %H:%M")} - {event.ends_at.astimezone().strftime("%H:%M")}  

---""")
            if event.description:
                with section():
                    ui.markdown(f"""
##### **About this event**  
{event.description}

---
""")
            if event.album_url:
                with section():
                    image_carousel(await get_album_urls(event.album_url))

            if event.video_url:
                with section():
                    ui.element('iframe').props(
                        f'src="{event.video_url}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen').classes('w-full h-auto aspect-16/9')

            if not event_passed:
                with section():
                    event_datetime_card(event)

                with section("Tickets"):
                    early_bird_active = event.early_bird_date > datetime.now(timezone.utc)
                    member_selected = logged_in and person.status == PersonStatus.member
                    early_bird_selected = early_bird_active and not member_selected
                    standard_selected = not early_bird_active and not member_selected

                    ticket_card("Members", event.member_ticket_price,
                                selected=member_selected)
                    ticket_card(
                        "Early Bird", event.early_bird_price, sold_out=not early_bird_active, selected=early_bird_selected)
                    ticket_card(
                        "Standard", event.general_admission_price, selected=standard_selected)

                    gtag_event("view_item_list", {
                        "items": [
                            {
                                "item_id": "ticket_member",
                                "price": event.member_ticket_price,
                            },
                            {
                                "item_id": "ticket_early_bird",
                                "price": event.early_bird_price,
                            },
                            {
                                "item_id": "ticket_standard",
                                "price": event.general_admission_price,
                            },
                        ]
                    })
                    fbq_event("ViewContent")

                with section():
                    location_card()

        ui.space().classes('h-[50px]')
        with section() as s:
            s.classes('fixed bottom-6 z-50')
            if event_passed:
                primary_button('This event has ended').props('disabled')
            else:
                btn = primary_button(
                    '🎟️ Buy your ticket', target=f'/buy-ticket?event_id={event.id}')
                if logged_in and person.status not in (PersonStatus.member, PersonStatus.verified):
                    btn.props(add='disable')
