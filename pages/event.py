import os
from uuid import UUID
from datetime import timezone, datetime
from nicegui import ui
from fastapi import HTTPException
from frame import frame
from consts import album_urls
from helpers import get_album_urls
from elements import (event_datetime_col, event_card, image_carousel,
                      secondary_button, section_title, ticket_price_col, toast, section)
from storage_cache import get_cache
import urllib

PHOTO_STORAGE_DIR = "photos"

maps_api_key = os.getenv('maps_api_key')


@ui.page('/event/{event_id}')
async def event_page(event_id):
    cache = get_cache()
    event = await cache.fetch_event(UUID(event_id))

    if not event:
        raise HTTPException(404)

    ui.page_title(f'{event.name} | Drop Dead Disco')
    venue = await cache.fetch_venue(event.venue_id)

    async with frame() as main_col:
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
            main_col.classes(add='gap-6 px-4 py-6')

            event_card(event, venue, show_venue=event_passed).classes(add='w-full')

            ui.label(event.description).classes('text-center')

            if not event_passed:
                async def buy_ticket():
                    if logged_in:
                        ui.navigate.to(f'/buy-ticket?event_id={event.id}')
                    else:
                        toast('Please sign in to continue', type='neutral')

                section_title("Date & time")
                event_datetime_col(event)
                if album_url:
                    with section("Vibe"):
                        image_carousel(await get_album_urls(album_url))
                with section("Tickets"):
                    ticket_price_col(event)
                    secondary_button('Get your ticket').on_click(buy_ticket)
            else:
                if album_url:
                    with section("As it happened"):
                        image_carousel(await get_album_urls(album_url))

                with section("Location"):
                    name_urlsafe = urllib.parse.quote(
                        venue.name, safe='/', encoding=None, errors=None)
                    ui.element('iframe').props(f'''
                        loading="lazy"
                        allowfullscreen
                        src="https://www.google.com/maps/embed/v1/place?q={name_urlsafe}&key={maps_api_key}"
                    ''').classes('rounded-3xl w-full max-w-96 aspect-square h-auto')

        else:
            ui.image(event.image_url).classes(
                'fixed top-0 left-0 w-full min-h-screen object-cover brightness-[0.25]')

            with ui.column().classes('gap-0 p-6 fixed inset-0 h-svh'):
                b = ui.label(event.starts_at.astimezone().strftime("%d.%m"))
                b.classes(replace='text-8xl font-medium text-white text-center')
