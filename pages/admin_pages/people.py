from uuid import UUID
from nicegui import ui
from helpers import parse_inputs
from consts import default_date_format, APP_BASE_URL
from api_models import PersonUpdate, EventTicketResponse, PersonCreate, EventTicketCreate, PersonResponse
from components import (primary_button, destructive_button, accented_button,
                        status_icon, page_header, section_title,
                        generate_form_from_model, ticket_indicator,
                        person_card, secondary_button)
from enums import PersonStatus
from services.person import create_person, update_person, delete_person
from services.event_ticket import create_event_ticket, delete_event_ticket, get_all_tickets, add_ticket_to_db
from services.event import get_all_events
from services.member_pass import get_all_member_passes
from services.person import get_all_persons, get_person
from db_models import EventTicket
from services.event_ticket import send_event_ticket


async def persons_panel():
    events = await get_all_events()
    persons = await get_all_persons()
    tickets = await get_all_tickets()
    member_passes = await get_all_member_passes()

    async def create_dialog():
        with ui.dialog(value=True) as dialog:
            with ui.card():
                section_title('New Person')
                form = generate_form_from_model(PersonCreate)

                async def submit():
                    data = await parse_inputs(form, PersonCreate)
                    try:
                        await create_person(PersonCreate(**data))
                        ui.navigate.reload()

                    except Exception as e:
                        ui.notify(f"Unable to create person: {str(e)}", type='negative')

                accented_button('Save').on_click(submit)
                primary_button('Cancel').on_click(dialog.close)

    with ui.row():
        ui.element('div').classes('w-[38px]')
        page_header('People')
        ui.icon('add', size='lg', color='secondary').on('click', create_dialog)

    sorted_events = sorted(events, key=lambda e: e.starts_at)

    event_ticket_person_map: dict[UUID, dict[UUID, EventTicketResponse]] = {
        e.id: {
            t.person_id: t for t in tickets if t.event_id == e.id
        }
        for e in sorted_events
    }

    categorized: dict[str, list[PersonResponse]] = {
        'pending': [],
        'members': [],
        'verified': [],
        'rejected': []
    }

    pass_map = {
        mp.person_id: mp.serial_number
        for mp in member_passes
    }

    for p in persons:
        if p.status == PersonStatus.pending:
            categorized['pending'].append(p)
        elif p.status == PersonStatus.member:
            categorized['members'].append(p)
        elif p.status == PersonStatus.verified:
            categorized['verified'].append(p)
        elif p.status == PersonStatus.rejected:
            categorized['rejected'].append(p)

    pending_persons = sorted(
        categorized['pending'],
        key=lambda p: p.first_name.lower()
    )

    members = sorted(
        categorized['members'],
        key=lambda p: pass_map.get(p.id)
    )

    verified_persons = sorted(
        categorized['verified'],
        key=lambda p: p.first_name.lower()
    )

    rejected_persons = sorted(
        categorized['rejected'],
        key=lambda p: p.first_name.lower()
    )

    def render_section(title: str, person_list: list, header=True):
        if not person_list:
            return

        section_title(f"{title} ({len(person_list)})")
        with ui.grid().classes('w-full justify-center gap-1 p-0'):
            if header:
                with ui.card().classes(f'cursor-pointer w-full', remove='rounded-3xl').props('bordered flat'):
                    with ui.row(wrap=False):
                        ui.label("Name").classes('w-40 text-left')
                        with ui.row(wrap=False).classes(remove='w-full'):
                            for i, event in enumerate(sorted_events, 1):
                                with ui.element('div').classes('size-4'):
                                    ui.label(str(i)).classes('text-center')

            for p in person_list:
                with person_card(p):
                    with ui.row(wrap=False):
                        with ui.row(wrap=False).classes('justify-start'):
                            if p.avatar_url:
                                ui.image(p.avatar_url).classes('size-8 rounded-full')
                            ui.label(f"{p.first_name} {p.last_name}").classes('w-48 text-left')
                        if header:
                            with ui.row(wrap=False).classes(remove='w-full'):
                                for event in sorted_events:
                                    ticket = event_ticket_person_map.get(
                                        event.id, {}).get(p.id)

                                    if ticket:
                                        ticket_indicator(ticket, bool(ticket.attended_at))
                                    else:
                                        ticket_indicator(None, False)

    # Render sections in order
    render_section('In Review', pending_persons, header=False)
    render_section('Members', members)
    render_section('Verified', verified_persons)
    render_section('Rejected', rejected_persons, header=False)


async def person_details_panel(person_id):
    person = await get_person(person_id)

    async def create_dialog():
        with ui.dialog(value=True) as dialog:
            with ui.card().classes('w-full gap-4 p-4'):
                section_title('Edit Person')
                original_data = person.__dict__
                form = generate_form_from_model(PersonUpdate, original_data)

                async def submit():
                    data = await parse_inputs(form, PersonUpdate)
                    changed_data = {
                        k: v for k, v in data.items()
                        if original_data.get(k) != v
                    }

                    if not changed_data:
                        ui.notify("No changes made")
                        return

                    try:
                        await update_person(person.id, PersonUpdate(**changed_data))
                        ui.notify("Person Updated")
                        await get_all_persons()
                        ui.navigate.reload()

                    except Exception as e:
                        ui.notify(f"Unable to update person: {str(e)}", type='negative')

                accented_button('Save').on_click(submit)
                primary_button('Cancel').on_click(dialog.close)

    async def create_ticket_dialog():
        events = await get_all_events()
        with ui.dialog(value=True) as dialog:
            with ui.card().classes('w-full gap-4 p-4'):
                section_title('Create Ticket')

                event_options = {str(e.id): f"{e.name} - {e.starts_at.astimezone().strftime(default_date_format)}"
                                 for e in sorted(events, key=lambda e: e.starts_at)}

                selected_event = ui.select(
                    options=event_options,
                    label='Select Event'
                )

                async def submit():
                    if not selected_event.value:
                        ui.notify("Please select an event", type='warning')
                        return

                    event_ticket = EventTicket(
                        person_id=person.id,
                        event_id=selected_event.value,
                    )

                    try:
                        if person.status == PersonStatus.verified:
                            await create_event_ticket(event_ticket)
                            await send_event_ticket(event_ticket)

                        elif person.status == PersonStatus.member:
                            await add_ticket_to_db(event_ticket)
                        ui.notify("Ticket created successfully", type='positive')
                        dialog.close()
                        ui.navigate.reload()

                    except Exception as e:
                        ui.notify(f"Unable to create ticket: {str(e)}", type='negative')

                accented_button('Create').on_click(submit)
                primary_button('Cancel').on_click(dialog.close)

    async def delete():
        if await ui.run_javascript('confirm("Are you sure you want to delete this person?")', timeout=10):
            try:
                await delete_person(person.id)
                ui.notify('Person deleted successfully.')
                await get_all_persons()
                ui.navigate.to('/gagodzya/people')
            except Exception as e:
                ui.notify(f'Error deleting person: {str(e)}')

    async def delete_ticket(id):
        if await ui.run_javascript('confirm("Are you sure you want to delete this ticket?")', timeout=10):
            try:
                await delete_event_ticket(id)
                ui.navigate.reload()
                ui.notify('Ticket deleted successfully.')
            except Exception as e:
                ui.notify(f'Error deleting ticket: {str(e)}')

    with ui.card():
        if person.avatar_url:
            ui.image(person.avatar_url).classes('size-20 rounded-full')
        page_header(f'{person.first_name} {person.last_name}')

        status_icon(person.status)
        ui.link(person.email, f"mailto:{person.email}").classes('text-lg')
        if person.instagram_handle:
            ui.link(f"@{person.instagram_handle}",
                    f"https://instagram.com/{person.instagram_handle}", new_tab=True).classes('text-lg')

        with ui.row().classes('justify-center'):
            primary_button('Edit').on_click(create_dialog)
            destructive_button('Delete').on_click(delete)
        secondary_button('Login as user', target=f"/login-as?person_id={person.id}")

    all_tickets = await get_all_tickets()
    person_tickets = [t for t in all_tickets if t.person_id == person.id]

    if person.status not in (PersonStatus.pending, PersonStatus.rejected):
        with ui.card():
            section_title('Tickets')

            events = await get_all_events()
            event_map = {e.id: e for e in events}

            sorted_tickets = sorted(
                person_tickets, key=lambda t: event_map[t.event_id].starts_at, reverse=True)

            with ui.grid().classes('flex justify-center gap-2 p-0'):
                for ticket in sorted_tickets:
                    event = event_map.get(ticket.event_id)
                    if event:
                        with ui.card():
                            with ui.row(wrap=False).classes('justify-between items-center w-full'):
                                ticket_indicator(ticket, bool(ticket.attended_at))
                                ui.link(
                                    event.name, target=f"{APP_BASE_URL}/pass/{person.id}").classes('text-lg font-semibold')
                                ui.icon('delete').on('click', lambda: delete_ticket(ticket.id))

            primary_button('Create Ticket').on_click(lambda: create_ticket_dialog())
