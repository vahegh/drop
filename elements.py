import secrets
import urllib.parse
from uuid import UUID
from datetime import datetime
from typing import Type, Union
from contextlib import contextmanager
from nicegui import ui, app
from pydantic import BaseModel, EmailStr
from api_models import EventResponse, MemberCardResponse, EventTicketResponse, EventResponse, VenueResponse, PersonResponse
from enums import PersonStatus
from helpers import generate_qr
from consts import (email_validation, insta_validation, name_validation,
                    email_non_required, email_placeholder, calendar_base_url,
                    google_calendar_img_url, instagram_placeholder, google_wallet_img_url,
                    apple_wallet_img_url, google_client_id, APP_BASE_URL)


ui.button.default_props(':ripple="false" :press-delay="0"')
ui.input.default_classes('w-full max-w-96 items-center justify-center')
ui.input.default_props('color=accent no-error-icon outlined clearable clear-icon="clear"')
ui.card.default_classes('rounded-3xl items-center')
ui.row.default_classes('w-full items-center justify-between')
ui.item.default_classes('text-3xl text-center')
ui.markdown.default_classes('text-base/relaxed w-full')
ui.link.default_classes('no-underline')
ui.separator.default_classes('w-full')


def rectangular_email_input(label="Email address", required=True, **kwargs):
    inp = ui.input(label=label, placeholder=email_placeholder, validation=email_validation, **kwargs).props(
        'type=email').on('blur', lambda: inp.validate()).without_auto_validation()
    if not required:
        inp._validation = email_non_required

    return inp


def rounded_email_input():
    inp = ui.input(placeholder=email_placeholder, validation=email_validation).props(
        'type=email rounded').classes('w-full').on('blur', lambda: inp.validate()).without_auto_validation()
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


def primary_button(text='', **kwargs):
    return ui.button(text, **kwargs).props(add='color="primary" rounded no-caps outline').classes('text-black h-[40px] w-full max-w-96')


def dark_button(text='', **kwargs):
    return ui.button(text, **kwargs).props(add='color="dark" rounded no-caps unelevated').classes('h-[40px] w-full max-w-96')


def secondary_button(text='', **kwargs):
    return ui.button(text, **kwargs).props(add='color="secondary" rounded no-caps unelevated').classes('h-[40px] w-full max-w-96')


def accented_button(text='', **kwargs):
    return ui.button(text, **kwargs).props(add='color="accent" rounded no-caps outline').classes('h-[40px] w-full max-w-96')


def destructive_button(text='', **kwargs):
    return ui.button(text, **kwargs).props(add='color="negative" rounded no-caps unelevated').classes('h-[40px] w-full max-w-96')


def positive_button(text='', **kwargs):
    return ui.button(text, **kwargs).props(add='color="positive" rounded no-caps unelevated').classes('h-[40px] w-full max-w-96')


def toast(text, timeout=1.5, **kwargs):
    ui.notification(text, timeout=timeout, **kwargs)


def event_datetime_col(event: EventResponse):
    col = ui.column().classes('items-center')
    with col:
        start_time_local = event.starts_at.astimezone()
        end_time_local = event.ends_at.astimezone()
        ui.label(start_time_local.strftime("%A %d %B")).classes('text-2xl')

        with ui.row().classes('flex px-8'):
            ui.label(start_time_local.strftime("%I %p").lstrip('0')
                     )
            ui.separator().props('color=secondary').classes('flex-1')
            ui.label(end_time_local.strftime("%I %p").lstrip('0')
                     )

        start_dt_google = event.starts_at.strftime("%Y%m%dT%H%M%SZ")
        end_dt_google = event.ends_at.strftime("%Y%m%dT%H%M%SZ")

        with primary_button("Add to Google Calendar", icon=f'img:{google_calendar_img_url}') as cal_btn:
            cal_btn.on_click(lambda: ui.navigate.to(
                f"{calendar_base_url}&dates={start_dt_google}/{end_dt_google}&details={urllib.parse.quote_plus(event.description)}&location=Yerevan&text={urllib.parse.quote_plus(event.name)}")
            )
    return col


def ticket_price_col(event: EventResponse):
    with ui.column().classes('w-full') as col:
        price_row("Members", event.member_ticket_price)
        if event.early_bird_date and event.early_bird_price:
            price_row(
                f"Early Bird (until {event.early_bird_date.strftime("%d.%m")})", event.early_bird_price)
        price_row("Standard", event.general_admission_price)
    return col


def event_card(event: EventResponse, venue: VenueResponse, show_venue=False):
    venue_name = venue.short_name if show_venue else "TBA"
    with ui.card().classes('rounded-[20px] p-0 w-64 max-w-96 aspect-4/5 h-auto flex-auto') as c:
        with ui.image(event.image_url).classes('event-card-img'):
            with ui.column().classes(add='bg-transparent h-full justify-between p-6 w-full'):
                page_header(event.name)
                with ui.row().classes('justify-between', remove='justify-center'):
                    ui.label(event.starts_at.astimezone().strftime('%d.%m'))
                    ui.label(venue_name)
    return c


def page_header(text=''):
    return ui.label(text).classes('text-3xl font-semibold')


def section_title(text=''):
    return ui.label(text).classes('text-xl font-medium')


def subsection_title(text=''):
    return ui.label(text).classes('text-lg font-medium')


def price_row(type, price):
    if price == 0:
        price_label = 'Free Entry'
    else:
        price_label = f"{price} AMD"

    with ui.row().classes('px-2 justify-between') as row:
        ui.label(type)
        ui.separator().classes('flex-1')
        ui.label(price_label).classes('font-bold')
    return row


status_colors = {
    PersonStatus.verified: "#11b553",
    PersonStatus.member: "#6233da",
    PersonStatus.rejected: "#d32629",
    PersonStatus.pending: "#f58302"
}


def ticket_indicator(exists: bool, used: bool):
    ticket_indicator = ui.element('div').classes('rounded size-4')
    if exists:
        bg_color = 'bg-green-500' if used else 'bg-orange-500'
        ticket_indicator.classes(add=bg_color)
    return ticket_indicator


def status_icon(status: PersonStatus):
    color = status_colors[status]
    return ui.label(status.value.upper()).classes(replace=f'text-[{color}] font-semibold')


def add_to_wallet(user_agent, google_url, apple_url) -> None:
    if user_agent == 'android':
        ui.image(google_wallet_img_url) \
            .classes('w-48') \
            .on('click', lambda: ui.navigate.to(google_url))
    elif user_agent == 'ios':
        ui.image(apple_wallet_img_url) \
            .classes('w-36') \
            .on('click', lambda: ui.navigate.to(apple_url))


def member_card(member_pass: MemberCardResponse, attendance: int, user_agent):
    img = generate_qr(member_pass.id)
    color = status_colors.get(PersonStatus.member)

    with ui.card().props('bordered flat').classes(f'w-full max-w-96 gap-4 px-0 justify-around border-[{color}]'):
        subsection_title('Your Membership pass')
        with ui.column().classes('w-full items-center px-6 py-0 gap-2'):
            with ui.row(wrap=False):
                with ui.column().classes(replace='gap-0'):
                    ui.label("Member ID")
                    ui.label(str(member_pass.serial_number).zfill(3)).classes('font-bold text-lg')
                with ui.column().classes(replace='gap-0'):
                    ui.label("Events")
                    ui.label(attendance).classes('text-right font-bold text-lg')
            ui.image(f'data:image/png;base64,{img}').classes('w-3/4')
            ui.label(f"Member since {member_pass.created_at.strftime("%B %Y")}".upper()).classes(
                f'text-[{color}] font-semibold')

        add_to_wallet(user_agent, member_pass.google_pass_url, member_pass.apple_pass_url)


def event_ticket(ticket: EventTicketResponse, event: EventResponse, user_agent):
    img = generate_qr(ticket.id)

    with ui.card().props('bordered flat').classes('w-full max-w-96 gap-4 px-0 justify-around border-black'):
        with ui.column().classes('gap-0 items-center'):
            ui.link(event.name, f"/event/{event.id}")
            subsection_title("Your ticket")
        with ui.column().classes('w-full items-center px-6 py-0'):
            ui.image(f'data:image/png;base64,{img}').classes('w-3/4 ')
            with ui.row(wrap=False):
                with ui.column().classes(replace='gap-0'):
                    ui.label("Event date")
                    ui.label(str(event.starts_at.astimezone().strftime("%d.%m"))
                             ).classes('font-bold text-lg')
                with ui.column().classes(replace='gap-0'):
                    ui.label("Start time")
                    ui.label(event.starts_at.astimezone().strftime("%H:%M")
                             ).classes('text-right font-bold text-lg')

        add_to_wallet(user_agent, ticket.google_pass_url, ticket.apple_pass_url)


def image_carousel(urls):
    with ui.carousel().classes('w-full h-96 aspect-square max-w-96 bg-gray-100').props('infinite autoplay="2500" swipeable animated arrows'):
        for url in urls:
            with ui.carousel_slide().classes('justify-center p-0'):
                ui.image(f'{url}=w1080-h1080').props('fit="cover"').classes('rounded-xl w-full h-full')


@contextmanager
def section(title: str = None, subtitle: str = None):
    with ui.column().classes('gap-2 p-0 w-full items-center justify-center max-w-96') as main:
        if title:
            with ui.column().classes('gap-0 items-center'):
                section_title(title).classes('text-center')
                if subtitle:
                    ui.label(subtitle).classes('text-center text-gray-600')
        yield main


TYPE_TO_NICEGUI = {
    str: lambda label: ui.input(label=label),
    EmailStr: lambda label: rectangular_email_input(label).props(remove='readonly'),
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
    card = ui.card().classes(
        f'w-full border-l-6 border-s-[{status_color}] cursor-pointer', remove='rounded-3xl').props('bordered flat')
    card.on('click', lambda p=person: ui.navigate.to(f'/gagodzya/person/{p.id}'))
    return card


def past_tickets_col(event_tickets, event_map):
    with section("Your past events"):
        if event_tickets:
            with ui.grid().classes('flex justify-center gap-2 p-0'):
                for ticket in event_tickets:
                    event = event_map.get(ticket.event_id)
                    if event:
                        with ui.card().classes('w-full max-w-96'):
                            with ui.row(wrap=False).classes('justify-between items-center w-full'):
                                ui.label(event.name).classes(
                                    'text-lg font-medium')
                                ticket_indicator(
                                    ticket, bool(ticket.attended_at))

        else:
            ui.markdown("""
                                        Usually this is where you'll see your tickets for past and upcoming events.  

                                        Since you don't have any, here's Colonel Hans Landa judging you silently.""")
            ui.element('iframe').props(
                'src="https://giphy.com/embed/9JeJxpaQlbcGC1zZNh"').classes('h-auto w-auto')


def instagram_dialog(instagram_info):
    with ui.dialog() as dl:
        with ui.card().classes('gap-4 w-full max-w-96'):
            if instagram_info:
                with section():
                    ui.link(
                        f"@{instagram_info['username']}", f"https://instagram.com/{instagram_info['username']}").classes('text-2xl')
                    ui.label(f"{instagram_info['followers']} followers").classes(
                        'text-gray-600')

                with section():
                    section_title("Is this you?")
                    with ui.row(wrap=False):
                        primary_button("No").on_click(lambda: dl.submit(False))
                        accented_button("Yes, submit").on_click(
                            lambda: dl.submit(True))
            else:
                with section(f"Instagram user {instagram_info['username']} not found", subtitle="Please check your username."):
                    primary_button("Fix").on_click(lambda: (dl.submit(False)))
    return dl


def google_button(text, url='/'):
    img_uri = app.add_static_file(local_file="static/images/google.svg")

    async def redirect_to_auth():
        csrf_token = secrets.token_urlsafe(32)
        app.storage.user['csrf_token'] = csrf_token

        params = {
            "client_id": google_client_id,
            "redirect_uri": f"{APP_BASE_URL}/google-login",
            "response_type": "code",
            "scope": "openid email profile",
            "hl": "en",
            "state": f"csrf_token={csrf_token}&url={url}"
        }

        auth_uri = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
        ui.navigate.to(auth_uri)

    with dark_button(text, icon=f'img:{img_uri}') as btn:
        btn.on_click(lambda: redirect_to_auth())

    return btn
