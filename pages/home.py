from nicegui import ui, app
from fastapi import Request
from datetime import timezone, datetime
from frame import frame
from storage_cache import get_cache
from api_models import EventResponse, PersonResponseFull
from components import (event_card, page_header, section_title,
                        status_icon, member_card, event_ticket,
                        image_carousel, google_button, primary_button,
                        section, past_tickets_col, accented_button,
                        status_colors)
from helpers import get_user_agent, get_album_urls, gtag
from enums import PersonStatus
from services.person import get_all_person_stats
from dependencies import Depends, logged_in
from services.drink_voucher import get_drink_vouchers_by_person_id
from services.drink import get_drink


@ui.page('/', title='Home | Drop Dead Disco', response_timeout=50)
async def home_page(request: Request, logged_in=Depends(logged_in)):

    video_h = "[20vh]" if logged_in else "[80vh]"

    async with frame(show_footer=True) as f:
        cache = get_cache()
        events = await cache.fetch_all_events()
        upcoming_events: list[EventResponse] = []
        past_events: list[EventResponse] = []

        for e in events:
            if e.ends_at >= datetime.now(timezone.utc):
                if e.shared:
                    upcoming_events.append(e)
            else:
                past_events.append(e)

        f.classes('pt-0')
        ui.video("/static/images/bg_video.mp4", controls=False).classes(
            f'object-cover h-{video_h} w-full').props('autoplay loop muted playsinline')

        if logged_in:
            person: PersonResponseFull = request.state.person
            vouchers = await get_drink_vouchers_by_person_id(person.id)
            with section():
                with ui.row(wrap=False).classes('flex max-w-96 px-4'):
                    with ui.column().classes('gap-0 items-start'):
                        status_icon(person.status)
                        page_header(person.full_name)

                    if person.avatar_url:
                        ui.image(person.avatar_url).classes(
                            'size-[64px] rounded-full flex-none')
                    else:
                        ui.icon('account_circle', size='64px', color="gray")

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
                            with section("Your ticket"):
                                event_ticket(next_event_ticket, next_event, user_agent)

                    if vouchers:
                        with section("Your drinks"):
                            for id, qty in vouchers.items():
                                drink = await get_drink(id)
                                with ui.card().classes(
                                        'w-full rounded-full h-[40px] py-0 justify-center items-center').props('flat'):
                                    with ui.row(wrap=False):
                                        ui.label(drink.name)
                                        ui.label(qty)

                    past_tickets_col(event_tickets, event_map)

                elif person.status == PersonStatus.member:
                    with section("Your Membership pass"):
                        member_card(person.member_pass, person.events_attended, user_agent)

                    if vouchers:
                        with section("Your drinks"):
                            for id, qty in vouchers.items():
                                drink = await get_drink(id)
                                with ui.card().classes(
                                        'w-full rounded-full h-[40px] py-0 justify-center items-center').props('flat'):
                                    with ui.row(wrap=False):
                                        ui.label(drink.name)
                                        ui.label(qty)

                    if person.drive_folder_url:
                        with section("You at Drop"):
                            ui.markdown(
                                "As a Member, you get access to **all photos of you** captured during Drop events, in full quality.").classes('text-center')
                            primary_button(
                                "Open in Google Photos", icon=f"img:/static/images/google_photos.svg", target=f"{person.drive_folder_url}?authuser={person.email}")
                            ui.markdown(
                                "*note: this album is only visible to you*").classes('text-center')

                    past_tickets_col(event_tickets, event_map)

                elif person.status == PersonStatus.pending:
                    with section("Review in progress"):
                        ui.image('/static/images/review.gif')
                        ui.markdown("""
                                We are working day and night to review all of your applications!  

                                We'll get back to you ASAP. You'll receive an email about your status.""").classes('text-center')

        else:
            with section("Wanna join the fun?", subtitle="Sign up to get verified."):
                google_button("Sign up with Google", request.url.path)

        if upcoming_events:
            page_header("Next event")
            for e in upcoming_events:
                with ui.link(target=f"/event/{e.id}").classes('w-full max-w-96 justify-center items-center'):
                    event_card(e)

        page_header("The Community")
        ui.markdown('''
**Drop Dead Disco** is a dance music community for those who want more from a night out.  
We host our events in unexpected locations - whatever has the most sparkle.  
We don't tell you the location beforehand, and every guest has to pass **verification** before they're able to buy tickets and attend.
''').classes('text-center px-4 max-w-[800px]')
        accented_button("Read more", target='/about')

        with ui.grid().classes('flex w-full justify-center p-2 gap-4'):
            with section("Stats", subtitle="Our community numbers as of right now.") as s:
                s.classes('px-4')
                person_counts = await get_all_person_stats()

                with ui.row(wrap=False):
                    ui.label("MEMBERS").classes('font-semibold text-gray-500')
                    ui.label(person_counts[PersonStatus.member]).classes(
                        f'text-3xl font-semibold text-[{status_colors.get(PersonStatus.member)}]')
                with ui.row(wrap=False):
                    ui.label("VERIFIED").classes('font-semibold text-gray-500')
                    ui.label(person_counts[PersonStatus.verified]).classes(
                        f'text-3xl font-semibold text-[{status_colors.get(PersonStatus.verified)}]')

            with section():
                album_url = "https://photos.google.com/share/AF1QipNb8__JbXtuax9DJm21Ca666tb2o4voA1u09nj0Z04jhyNjfdzcQ-1KTMqI7N9zNA?key=MG11Qm01N1JRWGxZUElGazdvcGlzOEw4VWVobUdR"
                image_carousel(await get_album_urls(album_url))

        page_header("Previous events")
        with ui.grid().classes('flex w-full justify-center p-2 gap-4'):
            for e in past_events:
                with ui.link(target=f"/event/{e.id}").classes('w-full max-w-96 justify-center items-center'):
                    event_card(e)

        section_title("Find us on Spotify")
        ui.element('iframe').props('''
                                    src="https://open.spotify.com/embed/playlist/49t6kUgW6nB7Kcv4d357qy?utm_source=generator"
                                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                                    loading="lazy"''').classes('rounded-xl w-full h-[500px] px-2')
