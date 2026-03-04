from nicegui import ui
from fastapi import Request, HTTPException
from datetime import timezone, datetime, timedelta
from frame import frame
from api_models import EventResponse, PersonResponseFull
from components import (event_card, page_header, section_title,
                        status_icon, member_card, event_ticket,
                        image_carousel, google_button, primary_button,
                        section, past_tickets_col, outline_button,
                        status_colors, name_input, instagram_input, rectangular_email_input,
                        outline_google_button, section_subtitle)
from helpers import get_user_agent, get_album_urls, gtag_event, fbq_event
from enums import PersonStatus
from services.person import get_all_person_stats, PersonCreate, create_person, get_person_by_email
from dependencies import Depends, logged_in
from services.drink_voucher import get_drink_vouchers_by_person_id
from services.drink import get_drink
from services.event import get_all_events, get_next_event
from services.venue import get_venue_info
from routes.attendance import get_attendance


@ui.page('/', title='Home | Drop Dead Disco', response_timeout=50)
async def home_page(request: Request, logged_in=Depends(logged_in)):
    async with frame(show_footer=True):
        events = await get_all_events()
        upcoming_events: list[EventResponse] = []
        past_events: list[EventResponse] = []
        next_event = await get_next_event()

        for e in events:
            if e.ends_at >= datetime.now(timezone.utc):
                if e.shared:
                    upcoming_events.append(e)
            else:
                past_events.append(e)

        if logged_in:
            person: PersonResponseFull = request.state.person
            # vouchers = await get_drink_vouchers_by_person_id(person.id)
            with section():
                with ui.row(wrap=False).classes('flex max-w-96 px-4'):
                    with ui.column().classes('gap-0 items-start'):
                        status_icon(person.status)
                        page_header(person.full_name).classes(remove='text-center')

                    if person.avatar_url:
                        ui.image(person.avatar_url).classes(
                            'size-[64px] rounded-full flex-none')
                    else:
                        ui.icon('account_circle', size='64px', color="gray")

            async def refer_person():
                with ui.dialog(value=True) as dl:
                    with ui.card():
                        with section("Your friend's info"):
                            with ui.column().classes('w-full gap-0'):
                                with ui.row(wrap=False):
                                    fn_inp = name_input("First name", "John")
                                    ln_inp = name_input("Last name", "Doe")
                                email_inp = rectangular_email_input()
                                insta_inp = instagram_input()
                                submit_btn = primary_button('Submit')

                async def submit():
                    if not all([
                        fn_inp.validate(),
                        ln_inp.validate(),
                        email_inp.validate(),
                        insta_inp.validate()
                    ]):
                        return

                    submit_btn.props(add='loading disable')

                    first_name = fn_inp.value.strip()
                    last_name = ln_inp.value.strip()
                    email = email_inp.value.strip()
                    insta = insta_inp.value.strip().lstrip('@')

                    existing_person = await get_person_by_email(email)
                    if existing_person:
                        ui.notify("This email address is already registered.", type='warning')
                        submit_btn.props(remove='loading disable')
                        return

                    payload = PersonCreate(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        instagram_handle=insta,
                        referer_id=person.id
                    )

                    new_person = await create_person(payload)

                    if new_person:
                        gtag_event("refer_friend", {"person_id": str(person.id)})
                        fbq_event("CompleteRegistration")
                        dl.clear()
                        with dl:
                            with ui.card():
                                with section("Success!", subtitle="Your friend has been registered and approved."):
                                    if next_event:
                                        primary_button("🎟️ Buy them a ticket",
                                                       target=f"/buy-ticket?event_id={next_event.id}")
                                    outline_button("Back to homepage").on_click(dl.close)

                    else:
                        dl.clear()
                        with dl:
                            with ui.card():
                                with section("Unknown error occured.", subtitle="Please try again a little later."):
                                    primary_button("Back").on_click(dl.close)

                submit_btn.on_click(lambda: submit())

            user_agent = await get_user_agent(request)

            event_tickets = person.event_tickets
            event_map = {e.id: e for e in events}

            if person.status == PersonStatus.verified:
                if next_event:
                    next_event_ticket = next(
                        (t for t in event_tickets if t.event_id == next_event.id), None)

                    if next_event_ticket:
                        venue = None
                        if datetime.now(timezone.utc) + timedelta(1) >= next_event.starts_at:
                            venue = await get_venue_info(next_event.venue_id)

                        with section("Your ticket", subtitle="Show this at the entrance, add to your Wallet for location and other updates", sep=True):
                            event_ticket(person.full_name, next_event_ticket,
                                         next_event, user_agent, venue)

                    else:
                        with section("Still no ticket?", subtitle=f"Get yours to join us at {next_event.name}", sep=True):
                            primary_button("🎟️ Buy your ticket",
                                           target=f"/buy-ticket?event_id={next_event.id}")

                person_attendance = await get_attendance(person.id)
                if person_attendance >= 2:
                    with section("Bring a friend!", subtitle="Since you have attended 2 or more Drops, you can refer a friend to join us", sep=True):
                        primary_button("Enter details").on_click(
                            lambda: refer_person())

                # if vouchers:
                #     with section("Your drinks"):
                #         for id, qty in vouchers.items():
                #             drink = await get_drink(id)
                #             with ui.card().classes(
                #                     'w-full rounded-full h-[40px] py-0 justify-center items-center').props('flat'):
                #                 with ui.row(wrap=False):
                #                     ui.label(drink.name)
                #                     ui.label(qty)

                past_tickets_col(event_tickets, event_map)

            elif person.status == PersonStatus.member:
                with section("Your Membership pass", subtitle="Use this to enter any Drop event", sep=True):
                    member_card(person.member_pass, person.events_attended, user_agent)

                with section("Bring a friend!", subtitle="As a Member, you can refer a friend to join us.", sep=True):
                    primary_button("Enter details").on_click(
                        lambda: refer_person())

                # if vouchers:
                #     with section("Your drinks"):
                #         for id, qty in vouchers.items():
                #             drink = await get_drink(id)
                #             with ui.card().classes(
                #                     'w-full rounded-full h-[40px] py-0 justify-center items-center').props('flat'):
                #                 with ui.row(wrap=False):
                #                     ui.label(drink.name)
                #                     ui.label(qty)

                if person.drive_folder_url:
                    with section("You at Drop", subtitle="As a Member, you get access to all photos of you captured during Drop events, in full quality.", sep=True):
                        outline_button(
                            "Open in Google Photos", icon=f"img:/static/images/google_photos.svg", target=f"{person.drive_folder_url}?authuser={person.email}")
                        ui.markdown(
                            "*note: this album is only visible to you*").classes('text-center text-sm')

                past_tickets_col(event_tickets, event_map)

            elif person.status == PersonStatus.pending:
                with section("Review in progress", sep=True):
                    ui.image('/static/images/review.gif')
                    ui.markdown("""
                            We are working day and night to review all of your applications!  

                            We'll get back to you ASAP. You'll receive an email about your status.""").classes('text-center')

            ui.separator()
        if upcoming_events:
            section_title("Next event")
            for e in upcoming_events:
                with section():
                    event_card(e)

        with section("The community"):
            ui.markdown('''
Drop Dead Disco is a hand-picked community hosting dance parties in secret locations around Yerevan.  
Every guest has to pass **verification** before they're able to buy tickets and attend.  
[Read more](/about)  
''')

        if not logged_in:
            with section("Wanna join the fun?", subtitle="Sign up to get verified"):
                with ui.row(wrap=False).classes('gap-2'):
                    google_button("Sign up", request.url.path)
                    outline_google_button("Log in", request.url.path)

        with section("People", subtitle="Live stats from the community", sep=True):
            person_counts = await get_all_person_stats()

            with section():
                with ui.row(wrap=False):
                    ui.label("MEMBERS").classes('font-semibold')
                    ui.label(person_counts[PersonStatus.member]).classes(
                        f'text-xl font-semibold text-[{status_colors.get(PersonStatus.member)}]')
                with ui.row(wrap=False):
                    ui.label("VERIFIED").classes('font-semibold')
                    ui.label(person_counts[PersonStatus.verified]).classes(
                        f'text-xl font-semibold text-[{status_colors.get(PersonStatus.verified)}]')

            album_url = "https://photos.google.com/share/AF1QipNb8__JbXtuax9DJm21Ca666tb2o4voA1u09nj0Z04jhyNjfdzcQ-1KTMqI7N9zNA?key=MG11Qm01N1JRWGxZUElGazdvcGlzOEw4VWVobUdR"
            image_carousel(await get_album_urls(album_url))

        with section("Previous events", subtitle="Photos and videos from past events", sep=True):
            pass
        with ui.grid().classes('flex w-full justify-center p-2 pt-0 gap-4'):
            for e in past_events:
                event_card(e)

        with section("Playlist", subtitle="Updated regularly with your favourites", sep=True):
            ui.element('iframe').props('''
                data-testid="embed-iframe"
                style="border-radius:12px"
                src="https://open.spotify.com/embed/playlist/49t6kUgW6nB7Kcv4d357qy?utm_source=generator"
                width="100%"
                height="152"
                frameBorder="0"
                allowfullscreen=""
                allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                loading="eager"
            ''')
