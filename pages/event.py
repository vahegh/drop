import os
from datetime import timezone, datetime
from nicegui import ui
from fastapi import HTTPException
from frame import frame
from consts import album_urls
from helpers import get_album_urls
from components import (event_datetime_col, event_card, image_carousel, primary_button,
                        secondary_button, section_title, ticket_price_col, toast, section)
import urllib
from services.event import get_event_info
from services.venue import get_venue_info
from dependencies import Depends, logged_in

PHOTO_STORAGE_DIR = "photos"

maps_api_key = os.getenv('maps_api_key')


@ui.page('/event/{event_id}', response_timeout=10)
async def event_page(event_id, logged_in=Depends(logged_in)):
    event = await get_event_info(event_id)

    if not event:
        raise HTTPException(404)

    ui.page_title(f'{event.name} | Drop Dead Disco')

    async with frame():
        event_passed = event.ends_at < datetime.now(timezone.utc)

        album_url = album_urls.get(event_id)

        if event_passed and not album_url:
            ui.image(event.image_url).classes(
                'fixed top-0 left-0 w-full min-h-screen object-cover z-[10] brightness-50')
            with ui.column().classes('gap-0 p-6 fixed inset-0 h-svh z-[12] justify-center'):
                b = ui.label('Photos Coming Soon.')
                b.classes.clear()
                b.classes(
                    'text-7xl font-bold text-white text-center')
            return

        if event.shared:
            with section():
                event_card(event).classes(add='w-full')

            with section():
                ui.label(event.description)

            with ui.grid().classes('flex w-full justify-center p-2 gap-4'):
                if not event_passed:
                    with section():
                        event_datetime_col(event)

                    if album_url:
                        with section():
                            image_carousel(await get_album_urls(album_url))

                    with section("Tickets"):
                        ticket_price_col(event)

                    primary_button('Get your ticket').on_click(
                        lambda: ui.navigate.to(f'/buy-ticket?event_id={event.id}'))

                else:
                    if album_url:
                        with section():
                            image_carousel(await get_album_urls(album_url))

                    if event.video_url:
                        with section("DJ Set"):
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

        else:
            ui.image(event.image_url).classes(
                'fixed top-0 left-0 w-full min-h-screen object-cover brightness-[0.25]')

            with ui.column().classes('gap-0 p-6 fixed inset-0 h-svh'):
                b = ui.label(event.starts_at.astimezone().strftime("%d.%m"))
                b.classes(replace='text-8xl font-medium text-white text-center')
