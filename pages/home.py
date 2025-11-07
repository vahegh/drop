from nicegui import ui, app
from fastapi import Request
from datetime import timezone, datetime
from frame import frame
from storage_cache import get_cache
from api_models import EventResponse, PersonResponseFull
from elements import (event_card, page_header, section_title,
                      status_icon, member_card, event_ticket,
                      image_carousel, large_google_button,
                      primary_button, section, ticket_indicator,
                      status_colors)
from helpers import get_user_agent, get_album_urls
from enums import PersonStatus
from routes.person import get_all_person_stats
from uuid import UUID
from dependencies import Depends, logged_in


@ui.page('/', title='Home | Drop Dead Disco', response_timeout=50)
async def home_page(request: Request, logged_in=Depends(logged_in)):
    video_url = app.add_static_file(local_file="static/images/bg_video.mp4")
    ui.video(video_url, controls=False).classes(
        'w-full object-cover h-[60vh]').props('autoplay loop muted playsinline')
    ui.context.client.page_container.classes('relative -top-14')

    async with frame() as f:
        f.classes('gap-6')
        upcoming_events: list[EventResponse] = []
        past_events: list[EventResponse] = []

        cache = get_cache()
        events = await cache.get_all_events()
        await cache.get_all_venues()

        if logged_in:
            person: PersonResponseFull = request.state.person
            with section() as col:
                col.classes('w-full')
                with ui.row(wrap=False).classes('flex px-4 max-w-96 justify-start'):
                    if person.avatar_url:
                        ui.image(person.avatar_url).classes(
                            'size-14 rounded-full flex-none')

                    with ui.column().classes('gap-0').classes(''):
                        status_icon(person.status)
                        page_header(person.name)

            with ui.grid().classes('flex w-full justify-center p-4 gap-8'):
                user_agent = await get_user_agent(request)
                next_event = await cache.get_next_event()

                event_tickets = person.event_tickets
                attended_events = [t.event_id for t in event_tickets if t.attended_at]
                event_map = {e.id: e for e in events}

                if person.status == PersonStatus.verified:
                    next_event = await cache.get_event(UUID('21324509-cb82-4a6a-bab1-751d67dad583'))

                    if next_event:
                        next_event_ticket = next(
                            (t for t in event_tickets if t.event_id == next_event.id), None)

                        if next_event_ticket:
                            with section("Upcoming:"):
                                event_ticket(next_event_ticket, next_event, user_agent)

                    with section("Your past tickets"):
                        if event_tickets:
                            sorted_tickets = sorted(
                                event_tickets, key=lambda t: event_map[t.event_id].starts_at, reverse=True)

                            with ui.grid().classes('flex justify-center gap-2 p-0'):
                                for ticket in sorted_tickets:
                                    event = event_map.get(ticket.event_id)
                                    if event:
                                        with ui.card().props(remove='flat').classes('w-full max-w-96'):
                                            with ui.row(wrap=False).classes('justify-between items-center w-full'):
                                                ui.label(event.name).classes(
                                                    'text-lg font-semibold')
                                                ticket_indicator(
                                                    ticket, bool(ticket.attended_at))

                        else:
                            ui.markdown("""
                                        Usually this is where you'll see your tickets for past and upcoming events.  

                                        Since you don't have any, here's Colonel Hans Landa judging you silently.""")
                            ui.element('iframe').props(
                                'src="https://giphy.com/embed/9JeJxpaQlbcGC1zZNh"').classes('h-auto w-auto')

                elif person.status == PersonStatus.member:
                    with section("Your pass"):
                        member_card(person.member_pass, person.events_attended, user_agent)

                    if person.drive_folder_url:
                        with section("Your photos"):
                            svg_url = app.add_static_file(
                                local_file='static/images/google_drive.svg')

                            ui.markdown("""
                            As a Member, you get access to **all photos** of you captured during Drop events, in full quality.  

                            *note: this folder is only visible to you*""").classes('text-center')

                            primary_button("Open in Google Drive", icon=f"img:{svg_url}").on_click(
                                lambda: ui.navigate.to(person.drive_folder_url))

                    with section("Your past tickets"):
                        if event_tickets:
                            sorted_tickets = sorted(
                                event_tickets, key=lambda t: event_map[t.event_id].starts_at, reverse=True)

                            with ui.grid().classes('flex justify-center gap-2 p-0'):
                                for ticket in sorted_tickets:
                                    event = event_map.get(ticket.event_id)
                                    if event:
                                        with ui.card().props(remove='flat').classes('w-full max-w-96'):
                                            with ui.row(wrap=False).classes('justify-between items-center w-full'):
                                                ui.label(event.name).classes(
                                                    'text-lg font-semibold')
                                                ticket_indicator(
                                                    ticket, bool(ticket.attended_at))

                elif person.status == PersonStatus.pending:
                    with section("Review in progress"):
                        ui.image('static/images/review.gif')
                        ui.markdown("""
                                We are working day and night to review all of your applications!  

                                We'll get back to you ASAP. You'll receive an email about your status.""").classes('text-center')

        else:
            with section("Wanna join the fun?", subtitle="Sign up to get verified."):
                large_google_button(request.url.path)

        await ui.context.client.connected()

        with ui.grid().classes('flex w-full justify-center p-4 gap-8'):
            with section("The Community"):
                person_counts = await get_all_person_stats()

                with ui.column().classes('w-full gap-4 p-4'):
                    with ui.row(wrap=False):
                        ui.label("MEMBERS").classes('font-semibold text-gray-600')
                        ui.label(person_counts[PersonStatus.member]).classes(
                            f'text-3xl font-bold text-[{status_colors.get(PersonStatus.member)}]')
                    with ui.row(wrap=False):
                        ui.label("VERIFIED").classes('font-semibold text-gray-600')
                        ui.label(person_counts[PersonStatus.verified]).classes(
                            f'text-3xl font-bold text-[{status_colors.get(PersonStatus.verified)}]')
                    with ui.row(wrap=False):
                        ui.label("PENDING REVIEW").classes('font-semibold text-gray-600')
                        ui.label(person_counts[PersonStatus.pending]).classes(
                            f'text-3xl font-bold text-[{status_colors.get(PersonStatus.pending)}]')

            with section("Our people"):
                album_url = "https://photos.google.com/share/AF1QipNb8__JbXtuax9DJm21Ca666tb2o4voA1u09nj0Z04jhyNjfdzcQ-1KTMqI7N9zNA?key=MG11Qm01N1JRWGxZUElGazdvcGlzOEw4VWVobUdR"
                image_carousel(await get_album_urls(album_url))

        for e in events:
            if e.ends_at >= datetime.now(timezone.utc):
                upcoming_events.append(e)
            else:
                past_events.append(e)

        if upcoming_events:
            section_title("Next event").classes('w-full text-center')
            with ui.grid().classes('flex w-full items-center justify-center'):
                for e in upcoming_events:
                    event_card(e, venue, show_venue=False).on(
                        'click', lambda i, e=e: ui.navigate.to(f'/event/{e.id}'))

        section_title("Previous events").classes('w-full text-center')
        with ui.grid().classes('flex w-full justify-center p-4 gap-4'):
            for e in past_events:
                venue = await cache.get_venue(e.venue_id)
                c = event_card(e, venue, show_venue=True).on(
                    'click', lambda i, e=e: ui.navigate.to(f'/event/{e.id}'))
                if logged_in:
                    if e.id in attended_events:
                        c.classes(add='border-green-600')

        with section("Find us on Spotify"):
            ui.element('iframe').props('''
                                    src="https://open.spotify.com/embed/playlist/49t6kUgW6nB7Kcv4d357qy?utm_source=generator"
                                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                                    loading="lazy"''').classes('rounded-xl w-full max-w-[500px] aspect-4/5 h-auto')
