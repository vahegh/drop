from datetime import timezone, datetime
from nicegui import ui
from fastapi import HTTPException
from uuid import UUID
from frame import frame
from consts import album_urls
from helpers import get_album_urls, gtag_event
from components import (event_datetime_card, event_card, image_carousel, primary_button,
                        ticket_card, section, location_card, page_header)
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
async def event_page(event_id: UUID, logged_in=Depends(logged_in)):
    event = await get_event_info(event_id)
    if not event:
        raise HTTPException(404)

    if logged_in:
        person: PersonResponseFull = ui.context.client.request.state.person

    ui.page_title(f'{event.name} | Drop Dead Disco')

    async with frame():
        event_passed = event.ends_at < datetime.now(timezone.utc)
        album_url = album_urls.get(event_id)

        with section():
            event_card(event, share=True)

        with section():
            ui.markdown(event.description).classes('text-center')

        with ui.grid().classes('flex w-full justify-center p-2 gap-4'):
            if not event_passed:
                with section():
                    event_datetime_card(event)

                with section():
                    location_card()

                if album_url:
                    with section():
                        image_carousel(await get_album_urls(album_url))

                with section("Tickets"):
                    members = ticket_card("Members", event.member_ticket_price)
                    early_bird = ticket_card("Early Bird", event.early_bird_price)
                    standard = ticket_card("Standard", event.general_admission_price)
                    if logged_in:
                        if person.status == PersonStatus.member:
                            members.classes('border-2 border-blue-500')
                        elif person.status == PersonStatus.verified:
                            if event.early_bird_date > datetime.now(timezone.utc):
                                early_bird.classes('border-2 border-blue-500')
                            else:
                                standard.classes('border-2 border-blue-500')
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

            else:
                if album_url:
                    with section():
                        image_carousel(await get_album_urls(album_url))

                if event.video_url:
                    with section("Drop on Youtube"):
                        ui.element('iframe').props(
                            f'src="{event.video_url}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen').classes('w-full h-auto aspect-16/9')

        ui.space().classes('h-[50px]')
        with section() as s:
            s.classes('fixed bottom-6 z-50')
            if event_passed:
                primary_button('This event has ended').props('disabled')
            else:
                btn = primary_button(
                    'Get your ticket', target=f'/buy-ticket?event_id={event.id}')
                if logged_in and person.status not in (PersonStatus.member, PersonStatus.verified):
                    btn.props(add='disable')
