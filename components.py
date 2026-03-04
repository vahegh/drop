import os
import json
import urllib.parse
from datetime import datetime, timezone
from uuid import UUID
from datetime import datetime
from typing import Type, Union
from contextlib import contextmanager
from nicegui import ui, app
from pydantic import BaseModel, EmailStr
from api_models import EventResponse, MemberCardResponse, EventTicketResponse, EventResponse, VenueResponse, PersonResponse, CardBindingResponse
from enums import PersonStatus
from helpers import generate_qr, get_google_auth_url
from consts import (email_validation, insta_validation, name_validation,
                    email_non_required, email_placeholder, calendar_base_url,
                    google_calendar_img_url, instagram_placeholder, APP_BASE_URL,
                    gmail_validation)
from helpers import get_card_type, gtag_event, share_event

maps_api_key = os.getenv('maps_api_key')

status_colors = {
    PersonStatus.verified: "#00c951",
    PersonStatus.member: "#ad46ff",
    PersonStatus.rejected: "#fb2c36",
    PersonStatus.pending: "#ff6900"
}

ui.button.default_props(':ripple="false" :press-delay="0"')
ui.input.default_classes('w-full max-w-96 items-center justify-center')
ui.input.default_props('color=accent no-error-icon outlined clearable clear-icon="clear"')
ui.card.default_classes('rounded-3xl items-center w-full')
ui.row.default_classes('w-full items-center justify-between')
ui.item.default_classes('text-3xl text-center')
ui.markdown.default_classes('text-base/relaxed w-full')
ui.separator.default_classes('w-full')
ui.radio.default_props(''':color="Quasar.Dark.isActive ? 'light' : 'dark'"''')
ui.link.default_classes('no-underline')
ui.image.default_props('no-spinner')
ui.select.default_classes('w-full')


# Inputs
def rectangular_email_input(label="Email address", required=True, **kwargs):
    inp = ui.input(label=label, placeholder=email_placeholder, validation=email_validation, **kwargs).props(
        'type=email').without_auto_validation()
    if not required:
        inp._validation = email_non_required

    return inp


def rectangular_gmail_input(label="Email address", required=True, **kwargs):
    inp = ui.input(label=label, placeholder=email_placeholder, validation=gmail_validation, **kwargs).props(
        'type=email').without_auto_validation()
    if not required:
        inp._validation = email_non_required

    return inp


def rounded_email_input():
    inp = ui.input("Add a friend", placeholder=email_placeholder, validation=email_validation).props(
        'type=email rounded').classes('w-full').without_auto_validation()
    return inp


def instagram_input():
    inp = ui.input(label="Instagram username", placeholder=instagram_placeholder, validation=insta_validation
                   ).props('prefix="@"').on('blur', lambda: inp.validate()).without_auto_validation()
    return inp


def name_input(label, placeholder, **kwargs):
    inp = ui.input(
        label=label,
        placeholder=placeholder,
        validation=name_validation,
        **kwargs
    ).on('blur', lambda: inp.validate()).without_auto_validation()
    return inp


# Buttons
def primary_button(text='', target=None, **kwargs):
    btn = ui.button(text, color=None, **kwargs).classes('h-[40px] w-full max-w-96')
    btn.props(add='''rounded no-caps unelevated :color="Quasar.Dark.isActive ? 'light' : 'dark'"''')
    btn.props(add=''':text-color="Quasar.Dark.isActive ? 'black' : 'light'"''')
    if target:
        btn.props(add=f'href={target}')
    return btn


def secondary_button(text='', target=None, **kwargs):
    btn = ui.button(
        text, **kwargs).props(add='color="secondary" rounded no-caps unelevated').classes('h-[40px] w-full max-w-96')
    if target:
        btn.props(add=f'href={target}')
    return btn


def positive_button(text='', target=None, **kwargs):
    btn = ui.button(
        text, **kwargs).props(add='color="positive" rounded no-caps unelevated').classes('h-[40px] w-full max-w-96')
    if target:
        btn.props(add=f'href={target}')
    return btn


def destructive_button(text='', target=None, **kwargs):
    btn = ui.button(
        text, **kwargs).props(add='color="negative" rounded no-caps unelevated').classes('h-[40px] w-full max-w-96')
    if target:
        btn.props(add=f'href={target}')
    return btn


def accented_button(text='', target=None, **kwargs):
    btn = ui.button(
        text, **kwargs).props(add='color="accent" rounded no-caps outline').classes('h-[40px] w-full max-w-96')
    if target:
        btn.props(add=f'href={target}')
    return btn


def outline_button(text='', target=None, **kwargs):
    btn = ui.button(text, color=None, **
                    kwargs).props(add='rounded no-caps outline').classes('h-[40px] w-full max-w-96 backdrop-blur-sm')
    if target:
        btn.props(add=f'href={target}')
    return btn


def login_button(target):
    btn = ui.button("Sign up", color=None)
    btn.props(f'size="12px" outline rounded no-caps href={target}')
    return btn


def event_card(event: EventResponse):
    with ui.link(target=f"/event/{event.id}").classes('w-full max-w-96 justify-center items-center') as c:
        with ui.image(event.image_url).classes('aspect-4/5 rounded-3xl w-full max-w-96 items-center'):
            page_header(event.name).classes('bg-transparent w-full')
    return c


def event_datetime_card(event: EventResponse):
    with ui.card().classes('p-0 bg-transparent').props('flat') as card:
        event_duration = (event.ends_at - event.starts_at).total_seconds()
        elapsed = (datetime.now(timezone.utc) - event.starts_at).total_seconds()
        progress_value = 0
        if elapsed > 0:
            progress_value = elapsed / event_duration

        with section(event.starts_at.astimezone().strftime("%A, %d %B")):
            with ui.row(wrap=False).classes('px-4 gap-2'):
                ui.label(event.starts_at.astimezone().strftime("%I %p").lstrip('0')
                         )
                ui.linear_progress(value=progress_value, show_value=False, size='2px',
                                   color='positive').classes('flex-1')
                ui.label(event.ends_at.astimezone().strftime("%I %p").lstrip('0')
                         )

            start_dt_google = event.starts_at.strftime("%Y%m%dT%H%M%SZ")
            end_dt_google = event.ends_at.strftime("%Y%m%dT%H%M%SZ")

            desc = f"""{event.description}
            Tickets: {APP_BASE_URL}/buy-ticket?event_id={event.id}"""

            with ui.row(wrap=False).classes('gap-2'):
                outline_button(
                    "Add to Calendar",
                    icon=f'img:{google_calendar_img_url}',
                    target=f"{calendar_base_url}&dates={start_dt_google}/{end_dt_google}&details={urllib.parse.quote_plus(desc)}&location=Yerevan&text={urllib.parse.quote_plus(event.name)}"
                ).on_click(lambda: gtag_event("add_to_calendar"))
                with ui.button().props('flat round').on_click(lambda: share_event(event)):
                    ui.icon("ios_share")

    return card


def location_card():
    with ui.card().classes('p-0 bg-transparent').props('flat') as card:
        with section("Location", subtitle="Kentron, Yerevan"):
            ui.element('iframe').props(f'''
                loading="lazy"
                src="https://www.google.com/maps/embed/v1/place?q=Kentron&key={maps_api_key}"
            ''').classes('rounded-3xl w-full aspect-square h-auto invert-90 hue-rotate-180')
            section_subtitle(
                "Exact location will be provided to ticket holders 24h in advance.")

    return card


def ticket_card(type, price, sold_out=False, selected=False):
    if price == 0:
        price_label = 'Free Entry'
    else:
        price_label = f"{price} AMD"

    with ui.card().props('flat bordered') as card:
        with ui.row(wrap=False):
            ui.label(type)
            if sold_out:
                card.classes(add='text-gray-500')
                ui.separator().classes('flex-1')
                ui.label("SOLD OUT").classes('text-xs font-bold')
            ui.separator().classes('flex-1')
            ui.label(price_label).classes('font-bold')
    if selected:
        card.classes(add='border-2 border-blue-500')
    return card


def page_header(text=''):
    return ui.label(text).classes('text-3xl font-semibold text-center')


def page_subheader(text=''):
    return ui.label(text).classes('text-2xl font-semibold text-center')


def section_title(text=''):
    return ui.label(text).classes('text-2xl font-medium')


def subsection_title(text=''):
    return ui.label(text).classes('text-lg font-medium')


def section_subtitle(text=''):
    return ui.label(text).classes('text-center')


def ticket_indicator(exists: bool, used: bool):
    ticket_indicator = ui.element('div').classes('rounded size-2')
    if exists:
        bg_color = 'bg-positive' if used else 'bg-warning'
        ticket_indicator.classes(add=bg_color)
    return ticket_indicator


def status_icon(status: PersonStatus):
    color = status_colors[status]
    return ui.label(status.value.upper()).classes(replace=f'text-[{color}] font-semibold')


def add_to_wallet(user_agent, google_url, apple_url) -> None:
    if user_agent == 'android':
        outline_button("Add to Wallet", target=google_url,
                       icon="img:/static/images/google_wallet.svg")
    elif user_agent == 'ios':
        outline_button("Add to Wallet", target=apple_url,
                       icon="img:/static/images/apple_wallet.svg")


def member_card(member_pass: MemberCardResponse, attendance: int, user_agent):
    img = generate_qr(member_pass.id)
    color = status_colors.get(PersonStatus.member)

    with ui.card().props('bordered flat').classes(f'w-full max-w-96 gap-4 px-0 justify-around border-[{color}]'):
        with ui.column().classes('w-full items-center px-6 py-0 gap-2'):
            with ui.row(wrap=False):
                with ui.column().classes(replace='gap-0'):
                    ui.label("Member ID")
                    ui.label(str(member_pass.serial_number).zfill(3)).classes('font-bold text-lg')
                with ui.column().classes(replace='gap-0'):
                    ui.label("Events")
                    ui.label(attendance).classes('text-right font-bold text-lg')
            ui.image(f'data:image/png;base64,{img}').classes('w-3/4')
            with ui.row(wrap=False).classes('justify-center gap-2', remove='justify-between'):
                ui.label(f"MEMBER SINCE").classes('font-semibold')
                ui.label(member_pass.created_at.strftime("%B %Y").upper()).classes(
                    f'text-[{color}] font-semibold')

            with section():
                add_to_wallet(user_agent, member_pass.google_pass_url, member_pass.apple_pass_url)


def event_ticket(name, ticket: EventTicketResponse, event: EventResponse, user_agent, venue: VenueResponse = None):
    img = generate_qr(ticket.id)

    with ui.card().props('bordered flat').classes('w-full max-w-96 gap-4 px-0 justify-around border-black'):
        with ui.column().classes('gap-0 items-center'):
            section_title(name)
        with ui.column().classes('w-full items-center px-6 py-0'):
            ui.image(f'data:image/png;base64,{img}').classes('w-3/4')
            with ui.row(wrap=False):
                with ui.column().classes(replace='gap-0'):
                    ui.label("Event date")
                    ui.label(str(event.starts_at.astimezone().strftime("%d.%m"))
                             ).classes('font-bold text-lg')
                with ui.column().classes(replace='gap-0'):
                    ui.label("Start time")
                    ui.label(event.starts_at.astimezone().strftime("%H:%M")
                             ).classes('text-right font-bold text-lg')
            if venue:
                with ui.column().classes('w-full items-center gap-0'):
                    ui.label("Location")
                    ui.label(venue.name).classes('font-bold text-lg')

        with section():
            add_to_wallet(user_agent, ticket.google_pass_url, ticket.apple_pass_url)


def image_carousel(urls):
    with ui.carousel().classes('w-full max-w-96 bg-transparent h-auto ').props('infinite autoplay="2500" swipeable animated arrows'):
        for url in urls:
            with ui.carousel_slide().classes('justify-center p-0'):
                ui.image(f'{url}=w1080-h1080').props('fit="scale-down"').classes('w-full aspect-3/2')


@contextmanager
def section(title: str = None, subtitle: str = None, sep: bool = False):
    with ui.column().classes('gap-2 px-2 py-0 w-full items-center justify-start max-w-96') as main:
        if sep:
            ui.separator()
        if title:
            with ui.column().classes('gap-0 p-2 items-center'):
                section_title(title).classes('text-center')
                if subtitle:
                    section_subtitle(subtitle)
        yield main


TYPE_TO_NICEGUI = {
    str: lambda label: ui.input(label=label),
    EmailStr: lambda label: rectangular_gmail_input(label),
    int: lambda label: ui.number(label=label),
    float: lambda label: ui.number(label=label, step=0.1),
    bool: lambda label: ui.checkbox(text=label),
    datetime: lambda label: ui.input(label=label).props('type="datetime-local"'),
    UUID: lambda label: ui.input(label=label),
    PersonStatus: lambda label: ui.select(
        options={member: member.value for member in PersonStatus}, label=label)
}


def generate_form_from_model(model: Type[BaseModel], default_values={}, venues: list[VenueResponse] = None):
    form_elements = {}

    for field_name, field_info in model.model_fields.items():
        field_type = field_info.annotation
        if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
            field_type = next(t for t in field_type.__args__ if t is not type(None))
        if field_name == 'venue_id' and venues:
            options = {str(venue.id): venue.name for venue in venues}
            element = ui.select(options=options, label=field_name.replace('_', ' ').capitalize())
        else:
            component_factory = TYPE_TO_NICEGUI.get(field_type)
            element = component_factory(field_name.replace('_', ' ').capitalize())

        if field_name in default_values:
            value = default_values[field_name]
            if isinstance(value, UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.astimezone().strftime('%Y-%m-%dT%H:%M')
            element.value = value
        form_elements[field_name] = element
    return form_elements


def person_card(person: PersonResponse):
    status_color = status_colors.get(person.status)
    with ui.link(target=f'/gagodzya/person/{person.id}').classes('w-full'):
        card = ui.card().classes(
            f'w-full border-l-4 border-s-[{status_color}] p-2', remove='rounded-3xl').props('bordered flat')
    return card


def past_tickets_col(event_tickets, event_map):
    with section("Your attendance", sep=True):
        if event_tickets:
            with ui.grid().classes('flex justify-center gap-2 p-0 w-full max-w-96'):
                for ticket in event_tickets:
                    event = event_map.get(ticket.event_id)
                    if event:
                        with ui.card().classes('w-full').props('flat'):
                            with ui.row(wrap=False).classes('justify-between items-center w-full'):
                                ui.label(f"🎟️ {event.name}").classes(
                                    'text-lg font-medium')
                                ticket_indicator(
                                    ticket, bool(ticket.attended_at))

        else:
            ui.markdown("""
                                        Usually this is where you'll see your tickets for past and upcoming events.  

                                        Since you don't have any, here's Colonel Hans Landa judging you silently.""")
            ui.element('iframe').props(
                'src="https://giphy.com/embed/9JeJxpaQlbcGC1zZNh"').classes('h-auto w-full')


def instagram_dialog(instagram_info):
    with ui.dialog() as dl:
        with ui.card().classes('gap-4 w-full max-w-96'):
            with section():
                ui.link(
                    f"@{instagram_info['username']}", f"https://instagram.com/{instagram_info['username']}").classes('text-2xl')
                ui.label(f"{instagram_info['followers']} followers").classes(
                    'text-gray-600')

            with section():
                section_title("Is this you?")
                with ui.row(wrap=False):
                    outline_button("No").on_click(lambda: dl.submit(False))
                    primary_button("Yes, submit").on_click(
                        lambda: dl.submit(True))
    return dl


def google_button(text, url='/', login_hint=None):
    async def redirect_to_auth():
        auth_uri = await get_google_auth_url(url=url, login_hint=login_hint)
        ui.navigate.to(auth_uri)

    with primary_button(text, icon="img:/static/images/google.svg") as btn:
        btn.on_click(lambda: redirect_to_auth())

    return btn


def outline_google_button(text, url='/', login_hint=None):
    async def redirect_to_auth():
        auth_uri = await get_google_auth_url(url=url, login_hint=login_hint)
        ui.navigate.to(auth_uri)

    with outline_button(text, icon="img:/static/images/google.svg") as btn:
        btn.on_click(lambda: redirect_to_auth())

    return btn


def binding_card(card: CardBindingResponse):
    card_type = get_card_type(card.masked_card_number[:6])
    c = ui.card().classes(
        f'w-full rounded-full h-[40px] py-2').props('flat')
    with c:
        with ui.row(wrap=False):
            with ui.row(wrap=False).classes(remove='justify-between'):
                if card_type == 'visa':
                    ui.image('/static/images/visa.svg').classes('w-6')
                elif card_type == 'mastercard':
                    ui.image('/static/images/mastercard.svg').classes('w-6')
                else:
                    ui.icon('card')

                ui.label(f"{card_type.capitalize()} •••• {card.masked_card_number[-4:]}")

            exp_m = card.card_expiry_date[-2:]
            exp_y = card.card_expiry_date[2:4]
            ui.label(f"{exp_m}/{exp_y}")

    return c


@contextmanager
def payment_choice():
    with ui.row(wrap=False).classes('justify-center items-center gap-2'):
        yield
