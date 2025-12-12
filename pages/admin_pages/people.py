from nicegui import ui
from helpers import parse_inputs
from api_models import PersonUpdate, PersonCreate, PersonResponse
from components import (primary_button, destructive_button, positive_button,
                        status_icon, page_header, section_title,
                        generate_form_from_model, ticket_indicator,
                        person_card, section,
                        positive_button, outline_button)
from enums import PersonStatus
from services.person import create_person, update_person, delete_person
from services.event_ticket import create_event_ticket, delete_event_ticket, get_tickets_by_person_id, add_ticket_to_db
from services.event import get_all_events
from services.member_pass import get_all_member_passes
from services.person import get_all_persons, get_person
from db_models import EventTicket
from services.event_ticket import send_event_ticket


async def persons_panel():
    persons = await get_all_persons()
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

                positive_button('Save').on_click(submit)
                outline_button('Cancel').on_click(dialog.close)

    page_header('People')

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

    def render_section(title: str, person_list: list[PersonResponse]):
        if not person_list:
            return

        with section(f"{title} ({len(person_list)})"):
            for p in person_list:
                with person_card(p):
                    with ui.row(wrap=False):
                        with ui.row(wrap=False).classes('justify-start', remove='w-full'):
                            if p.avatar_url:
                                ui.image(p.avatar_url).classes('w-[32px] rounded-full')
                            else:
                                ui.icon('account_circle', size='32px', color="gray")
                            ui.label(f"{p.first_name} {p.last_name}").classes('w-48 text-left')

    render_section('In Review', pending_persons)
    primary_button("New person").on_click(create_dialog)
    render_section('Members', members)
    render_section('Verified', verified_persons)
    render_section('Rejected', rejected_persons)


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

                positive_button('Save').on_click(submit)
                outline_button('Cancel').on_click(dialog.close)

    async def create_ticket_dialog():
        events = await get_all_events()
        with ui.dialog(value=True) as dialog:
            with ui.card().classes('w-full gap-4 p-4'):
                section_title('Create Ticket')
                event_options = {e.id: e.name for e in events}

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

                positive_button('Create').on_click(submit)
                outline_button('Cancel').on_click(dialog.close)

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
                ui.notify('Ticket deleted successfully.')
                ui.navigate.reload()
            except Exception as e:
                ui.notify(f'Error deleting ticket: {str(e)}')

    with section():
        with section():
            if person.avatar_url:
                ui.image(person.avatar_url).classes('size-20 rounded-full')
            page_header(f'{person.first_name} {person.last_name}')
            status_icon(person.status)

        with section():
            ui.link(person.email, f"mailto:{person.email}").classes('text-lg')
            if person.instagram_handle:
                ui.link(f"@{person.instagram_handle}",
                        f"https://instagram.com/{person.instagram_handle}", new_tab=True).classes('text-lg')

        with section():
            with ui.row(wrap=False):
                outline_button('Edit person').on_click(create_dialog)
                destructive_button('Delete person').on_click(delete)

        with section():
            outline_button('Login as person', target=f"/login-as?person_id={person.id}")

    if person.status not in (PersonStatus.pending, PersonStatus.rejected):
        tickets = await get_tickets_by_person_id(person.id)
        with section("Tickets"):
            events = await get_all_events()
            event_map = {e.id: e for e in events}

            for ticket in tickets:
                event = event_map.get(ticket.event_id)
                if event:
                    with ui.card():
                        with ui.row(wrap=False):
                            ticket_indicator(ticket, bool(ticket.attended_at))
                            section_title(event.name)
                            ui.icon('delete').on('click', lambda t=ticket: delete_ticket(t.id))

            primary_button('Create Ticket').on_click(lambda: create_ticket_dialog())
