from nicegui import ui, app
from fastapi import Request
from datetime import timezone, datetime
from frame import frame
from storage_cache import get_cache
from api_models import EventResponse, PersonResponseFull
from elements import (event_card, page_header, section_title,
                      status_icon, member_card, event_ticket,
                      image_carousel, large_google_button,
                      primary_button, section, past_tickets_col, accented_button,
                      status_colors)
from helpers import get_user_agent, get_album_urls
from enums import PersonStatus
from routes.person import get_all_person_stats
from uuid import UUID
from dependencies import Depends, logged_in


@ui.page('/', title='Home | Drop Dead Disco', response_timeout=50)
async def home_page(request: Request, logged_in=Depends(logged_in)):
    async with frame() as f:

        f.classes('gap-2')
        upcoming_events: list[EventResponse] = []
        past_events: list[EventResponse] = []

        cache = get_cache()
        events = await cache.fetch_all_events()
        await cache.fetch_all_venues()

        video_url = app.add_static_file(local_file="static/images/bg_video.mp4")
        vid = ui.video(video_url, controls=False).classes(
            'w-full object-cover h-[80vh]').props('autoplay loop muted playsinline')
        ui.context.client.page_container.classes('relative -top-14')

        if logged_in:
            vid.classes(add='h-[20vh]', remove='h-[80vh]')
            person: PersonResponseFull = request.state.person
            with section():
                with ui.row(wrap=False).classes('flex max-w-96'):
                    if person.avatar_url:
                        ui.image(person.avatar_url).classes(
                            'size-16 rounded-full flex-none')

                    with ui.column().classes('gap-0 items-end'):
                        status_icon(person.status)
                        page_header(person.name).classes('text-right')

            ui.separator()
            with ui.grid().classes('flex w-full justify-center p-2 gap-4'):
                user_agent = await get_user_agent(request)
                next_event = await cache.fetch_next_event()

                event_tickets = person.event_tickets
                event_map = {e.id: e for e in events}

                if person.status == PersonStatus.verified:
                    if next_event:
                        next_event_ticket = next(
                            (t for t in event_tickets if t.event_id == next_event.id), None)

                        if next_event_ticket:
                            with section("Upcoming:"):
                                event_ticket(next_event_ticket, next_event, user_agent)

                    past_tickets_col(event_tickets, event_map)

                elif person.status == PersonStatus.member:
                    with section():
                        member_card(person.member_pass, person.events_attended, user_agent)

                    if person.drive_folder_url:
                        with section():
                            svg_url = app.add_static_file(
                                local_file='static/images/google_drive.svg')

                            ui.markdown(
                                "As a Member, you get access to **all photos of you** captured during Drop events, in full quality.").classes('text-center')
                            primary_button("Open in Google Drive", icon=f"img:{svg_url}").on_click(
                                lambda: ui.navigate.to(person.drive_folder_url))
                            ui.markdown(
                                "*note: this folder is only visible to you*").classes('text-center')

                    past_tickets_col(event_tickets, event_map)

                elif person.status == PersonStatus.pending:
                    with section("Review in progress"):
                        ui.image('static/images/review.gif')
                        ui.markdown("""
                                We are working day and night to review all of your applications!  

                                We'll get back to you ASAP. You'll receive an email about your status.""").classes('text-center')
        else:
            with section("Wanna join the fun?", subtitle="Sign up to get verified."):
                large_google_button(request.url.path)
        ui.separator()

        page_header("The Community")
        with ui.grid().classes('flex w-full justify-center p-2 gap-4'):
            with section():
                ui.markdown('''
**Drop Dead Disco** is a dance music community for those who want more from a night out. 

We host our events in unexpected locations - whatever has the most sparkle. 
                    
We don't tell you the location beforehand, and every guest has to pass **verification** before they're able to buy tickets and attend.
''').classes('text-md/5')
                accented_button("Read More").on_click(lambda: ui.navigate.to('/about'))

            with section("Stats"):
                person_counts = await get_all_person_stats()

                with ui.column().classes('w-full gap-4 px-4'):
                    with ui.row(wrap=False):
                        ui.label("MEMBERS").classes('font-semibold text-gray-600')
                        ui.label(person_counts[PersonStatus.member]).classes(
                            f'text-3xl font-semibold text-[{status_colors.get(PersonStatus.member)}]')
                    with ui.row(wrap=False):
                        ui.label("VERIFIED").classes('font-semibold text-gray-600')
                        ui.label(person_counts[PersonStatus.verified]).classes(
                            f'text-3xl font-semibold text-[{status_colors.get(PersonStatus.verified)}]')
                    # with ui.row(wrap=False):
                    #     ui.label("PENDING REVIEW").classes('font-semibold text-gray-600')
                    #     ui.label(person_counts[PersonStatus.pending]).classes(
                    #         f'text-3xl font-semibold text-[{status_colors.get(PersonStatus.pending)}]')

            with section():
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
        with ui.grid().classes('flex w-full justify-center p-2 gap-4'):
            for e in past_events:
                venue = await cache.fetch_venue(e.venue_id)
                event_card(e, venue, show_venue=True).on(
                    'click', lambda i, e=e: ui.navigate.to(f'/event/{e.id}'))

        section_title("Find us on Spotify")
        ui.element('iframe').props('''
                                    src="https://open.spotify.com/embed/playlist/49t6kUgW6nB7Kcv4d357qy?utm_source=generator"
                                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                                    loading="lazy"''').classes('rounded-xl w-full h-[500px] px-2')
