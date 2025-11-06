from nicegui import ui, app
from fastapi import Request
from datetime import timezone, datetime
from frame import frame
from storage_cache import get_cache
from api_models import EventResponse, EventTicketResponse, MemberCardResponse, PersonResponse
from elements import (event_card, page_header, section_title,
                      status_icon, member_card, event_ticket,
                      image_carousel, large_google_button,
                      primary_button, section, ticket_indicator,
                      status_colors)
from helpers import get_user_agent, get_album_urls
from enums import PersonStatus
from routes.person import get_all_person_stats


@ui.page('/', title='Home | Drop Dead Disco', response_timeout=50)
async def home_page(request: Request):
    video_url = app.add_static_file(local_file="static/images/bg_video.mp4")
    ui.video(video_url, controls=False).classes(
        'w-full object-cover h-[60vh]').props('autoplay loop muted playsinline')
    ui.context.client.page_container.classes('relative -top-14')

    async with frame() as (f, logged_in):
        f.classes('gap-4')

        upcoming_events: list[EventResponse] = []
        past_events: list[EventResponse] = []

        cache = get_cache()
        events = await cache.get_all_events()
        await cache.get_all_venues()

        if logged_in:
            st = app.storage.user
            person = PersonResponse(
                id=st['id'],
                name=st['name'],
                email=st['email'],
                instagram_handle=st['instagram_handle'],
                telegram_handle=st['telegram_handle'],
                status=PersonStatus(st['status']),
                avatar_url=st['avatar_url'],
                drive_folder_url=st['drive_folder_url']
            )

            with section("Your profile"):
                with ui.row(wrap=False).classes('flex px-4'):
                    with ui.column().classes('gap-0').classes('flex-auto'):
                        status_icon(person.status)
                        section_title(person.name)

                    ui.image(person.avatar_url).classes(
                        'size-14 rounded-full flex-none')

            user_agent = await get_user_agent(request)
            next_event = await cache.get_next_event()

            event_tickets = [EventTicketResponse(**t) for t in st['event_tickets']]
            attended_events = [t.event_id for t in event_tickets if t.attended_at]
            event_map = {e.id: e for e in events}

            if person.status == PersonStatus.verified:
                with section("Your tickets"):
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

                        if next_event:
                            next_event_ticket = next(
                                (t for t in event_tickets if t.event_id == next_event.id), None)

                            if next_event_ticket:
                                event_ticket(next_event_ticket, next_event, user_agent)
                        else:
                            ui.markdown("""
                                    Usually this is where you'll see your tickets for past and upcoming events.  

                                    Since you don't have any, here's Colonel Hans Landa judging you silently.""")
                            ui.element('iframe').props(
                                'src="https://giphy.com/embed/9JeJxpaQlbcGC1zZNh"').classes('h-auto w-auto')

            elif person.status == PersonStatus.member:
                member_pass = MemberCardResponse(**st['member_pass'])
                attendance = st['events_attended']
                with section("Your pass"):
                    member_card(member_pass, attendance, user_agent)

                if person.drive_folder_url:
                    with section("Your photos") as (_, heading):
                        svg_url = app.add_static_file(
                            local_file='static/images/google_drive.svg')
                        with heading:
                            heading.classes(add='items-center w-full')
                            ui.markdown("""
                            As a Member, you get access to **all photos** of you captured during Drop events, in full quality.  

                            *note: this folder is only visible to you*""").classes('text-center')

                        primary_button("Open in Google Drive", icon=f"img:{svg_url}").on_click(
                            lambda: ui.navigate.to(person.drive_folder_url))

            elif person.status == PersonStatus.pending:
                with section("Review in progress"):
                    ui.image('static/images/review.gif')
                    ui.markdown("""
                            We are working day and night to review all of your applications!  

                            We'll get back to you ASAP. You'll receive an email about your status.""").classes('text-center')

        else:
            with section("Wanna join the fun?", subtitle="Sign up to get verified.") as (_, heading):
                heading.classes(add='items-center')
                large_google_button(ui.context.client.request.url.path)

        with section("The Community"):
            album_url = "https://photos.google.com/share/AF1QipNb8__JbXtuax9DJm21Ca666tb2o4voA1u09nj0Z04jhyNjfdzcQ-1KTMqI7N9zNA?key=MG11Qm01N1JRWGxZUElGazdvcGlzOEw4VWVobUdR"
            image_carousel(await get_album_urls(album_url))

        with section("Stats"):
            person_counts = await get_all_person_stats()
            member_ct = person_counts[PersonStatus.member]
            verified_ct = person_counts[PersonStatus.verified]

            with ui.row().classes('w-full justify-center gap-4'):
                with ui.row(wrap=False).classes('items-center gap-2 justify-around'):
                    ui.label("MEMBERS").classes('font-semibold text-gray-600')
                    ui.label(member_ct).classes(
                        f'text-3xl font-bold text-[{status_colors.get(PersonStatus.member)}]')
                with ui.row(wrap=False).classes('items-center gap-2 justify-around'):
                    ui.label("VERIFIED").classes('font-semibold text-gray-600')
                    ui.label(verified_ct).classes(
                        f'text-3xl font-bold text-[{status_colors.get(PersonStatus.verified)}]')

        for e in events:
            if e.ends_at >= datetime.now(timezone.utc):
                upcoming_events.append(e)
            else:
                past_events.append(e)

        if upcoming_events:
            with section("Next event"):
                with ui.grid().classes('flex w-full items-center justify-center'):
                    for e in upcoming_events:
                        event_card(e, venue, show_venue=False).on(
                            'click', lambda i, e=e: ui.navigate.to(f'/event/{e.id}'))

        section_title("Previous events").classes('w-full text-center')
        for e in past_events:
            venue = await cache.get_venue(e.venue_id)
            c = event_card(e, venue, show_venue=True).on(
                'click', lambda i, e=e: ui.navigate.to(f'/event/{e.id}'))
            if logged_in:
                if e.id in attended_events:
                    c.classes(add='border-green-600')

        with section("Find us on Spotify", sep=False):
            ui.element('iframe').props('''
                                    src="https://open.spotify.com/embed/playlist/49t6kUgW6nB7Kcv4d357qy?utm_source=generator"
                                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                                    loading="lazy"''').classes('rounded-xl w-full max-w-[500px] aspect-4/5 h-auto')
