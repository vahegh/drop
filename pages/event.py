import os
from datetime import timezone, datetime
from nicegui import ui
from fastapi import HTTPException
from frame import frame
from consts import album_urls
from helpers import get_album_urls
from components import (event_datetime_col, event_card, image_carousel, primary_button,
                        ticket_price_col, section)
from services.event import get_event_info
from dependencies import Depends, logged_in
from api_models import PersonResponseFull
from enums import PersonStatus

PHOTO_STORAGE_DIR = "photos"

maps_api_key = os.getenv('maps_api_key')


@ui.page('/drop-5')
async def drop_5():
    ui.navigate.to("/event/d350a039-2316-41b4-9dfd-5d9c1e715d71")
    return


@ui.page('/event/{event_id}', response_timeout=10)
async def event_page(event_id, logged_in=Depends(logged_in)):
    event = await get_event_info(event_id)

    if not event:
        raise HTTPException(404)

    ui.page_title(f'{event.name} | Drop Dead Disco')

    async with frame():
        event_passed = event.ends_at < datetime.now(timezone.utc)

        album_url = album_urls.get(event_id)

        with section():
            event_card(event, share=True)

        with section("About the event"):
            ui.markdown(event.description)

        with ui.grid().classes('flex w-full justify-center p-2 gap-4'):
            if not event_passed:
                with section():
                    event_datetime_col(event)

                if album_url:
                    with section():
                        image_carousel(await get_album_urls(album_url))

                with section("Tickets"):
                    ticket_price_col(event)

            else:
                if album_url:
                    with section():
                        image_carousel(await get_album_urls(album_url))

                if event.video_url:
                    with section("Drop on Youtube"):
                        ui.element('iframe').props(
                            f'src="{event.video_url}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen').classes('w-full h-auto aspect-16/9')

                # with section("Location"):
                #     name_urlsafe = urllib.parse.quote(
                #         venue.name, safe='/', encoding=None, errors=None)
                #     ui.element('iframe').props(f'''
                #         loading="lazy"
                #         allowfullscreen
                #         src="https://www.google.com/maps/embed/v1/place?q={name_urlsafe}&key={maps_api_key}"
                #     ''').classes('rounded-3xl w-full max-w-96 aspect-square h-auto')

        ui.space().classes('h-[40px]')
        with section() as s:
            s.classes('fixed bottom-6 z-50')
            if event_passed:
                primary_button('This event has ended').props('disabled')
            else:
                if logged_in:
                    person: PersonResponseFull = ui.context.client.request.state.person
                    if person.status in (PersonStatus.member, PersonStatus.verified):
                        primary_button('Get your ticket', target=f'/buy-ticket?event_id={event.id}')
                    else:
                        primary_button('You can buy a ticket after verification')
                else:
                    primary_button('Sign up to get your ticket',
                                   target=f'/buy-ticket?event_id={event.id}')
