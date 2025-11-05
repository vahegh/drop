from datetime import datetime, timezone
from nicegui import ui, app
from fastapi import Request
from httpx import HTTPStatusError
from nicegui.elements.button import Button
from frame import frame
from enums import PaymentProvider, PersonStatus
from api_models import PersonResponse, PaymentCreate, ValidateTokenRequest
from helpers import get_user_agent
from elements import (rounded_email_input, secondary_button, primary_button, toast, event_datetime_col,
                      page_header, section_title)

from storage_cache import get_cache
from uuid import UUID


@ui.page('/buy-ticket', title='Buy Your Ticket | Drop Dead Disco')
async def buy_ticket_page(request: Request, event_id: UUID):
    st = app.storage.user
    cache = get_cache()

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

    event = await cache.get_event(event_id)

    # await client.notify_payment_page(person)

    user_agent = await get_user_agent(request)

    attendees = [person]

    async def send_pass(person: PersonResponse, btn: Button):
        btn.props(add='loading')
        try:
            if person.status == PersonStatus.approved:
                await client.create_event_ticket(person.id, event.id)
            elif person.status == PersonStatus.member:
                await client.create_member_pass(person.id)
            toast(f"Successfully sent pass to {person.email}.")
        except HTTPStatusError:
            toast("Failed to resend pass. Please try again later.", type='negative')
        finally:
            btn.props(remove='loading')

    async def main_page():
        main_col.classes(add='gap-3 p-3')

        async def buy_ticket(payment_provider: PaymentProvider, button: ui.button):
            amount = update_totals()
            if amount == 0:
                toast('0 AMD? really?', type='warning')
                return
            button.props(add='loading')
            ticket_holders = [a.id for a in attendees]
            payment_req = PaymentCreate(
                person_id=person.id,
                event_id=event.id,
                amount=amount,
                provider=payment_provider,
                ticket_holders=ticket_holders
            )

            try:
                url = await client.init_payment(payment_req)
            except HTTPStatusError as e:
                if e.response.status_code == 409:
                    main_col.clear()
                    with main_col:
                        existing_page()
                    return
            else:
                ui.navigate.to(url)
            finally:
                button.props(remove='loading')

        def update_totals():
            ticket_price = event.general_admission_price if datetime.now(
                timezone.utc) > event.early_bird_date else event.early_bird_price

            total_price = 0
            totals['members'] = 0
            totals['non_members'] = 0

            for p in attendees:
                if p.status == PersonStatus.member:
                    total_price += event.member_ticket_price
                    totals['members'] += 1
                elif p.status == PersonStatus.approved:
                    total_price += ticket_price
                    totals['non_members'] += 1

            member_no_label.text = str(totals['members'])
            non_member_no_label.text = str(totals['non_members'])
            quantity_label.text = str(totals['members'] + totals['non_members'])
            total_price_label.text = f"{total_price:,d} AMD"

            return total_price

        async def validate_and_add_attendee():
            email = add_attendee_input.value.strip()

            if not add_attendee_input.validate():
                return
            save_btn.props(add='loading')

            for i, att in enumerate(attendees):
                if att.email == email:
                    attendee_card = next((x for n, x in enumerate(
                        attendee_list_container.descendants()) if n == i), None)
                    attendee_card.classes(add='pulse-animation')
                    save_btn.props(remove='loading')
                    ui.timer(0.5, lambda: attendee_card.classes(
                        remove='pulse-animation'), once=True)
                    return

            new_attendee = await client.fetch_person_by_email(email)
            if not new_attendee:
                toast('This person has not applied for review', type='warning')
                save_btn.props(remove='loading')
                return

            if new_attendee.status in (PersonStatus.approved, PersonStatus.member):
                if await client.fetch_ticket_by_person_id(new_attendee.id, event.id):
                    with ui.dialog(value=True) as dl:
                        with ui.card().classes('bg-indigo-50'):
                            ui.label(f"The person you entered already has a ticket for {event.name}.").classes(
                                'text-lg')
                            primary_button("Back").on_click(dl.close)
                            save_btn.props(remove='loading')
                else:
                    attendees.append(new_attendee)
                    update_attendee_list()
                    update_totals()

                add_attendee_input.set_value('')
            else:
                toast('Can\'t buy a ticket for this person', type='warning')

            save_btn.props(remove='loading')

        def show_add_attendee_input():
            add_button.set_visibility(False)
            add_attendee_input.run_method('focus')
            add_attendee_row.set_visibility(True)

        def hide_add_attendee_input():
            add_button.set_visibility(True)
            add_attendee_row.set_visibility(False)

        def remove_attendee(attendee_to_remove):
            attendees.remove(attendee_to_remove)
            update_totals()
            update_attendee_list()

        def update_attendee_list():
            attendee_list_container.clear()
            with attendee_list_container:
                for attendee in attendees:
                    with ui.card().classes('w-full items-center justify-center bg-transparent rounded-full').props('bordered'):
                        with ui.row(wrap=False).classes('gap-1') as email_row:
                            ui.label(f'{attendee.email}').classes(
                                ' text-sm')
                        if attendee == person:
                            with email_row:
                                ui.label("You").classes('ml-auto text-green-700')
                        else:
                            with email_row:
                                ui.icon('close').classes('cursor-pointer ml-auto').on('click',
                                                                                      lambda a=attendee: remove_attendee(a))

        page_header(event.name)
        event_datetime_col(event)

        with ui.row(wrap=False).classes('gap-2 justify-center'):
            section_title('Attendees')
            with ui.icon('help_outline', size='xs'):
                ui.tooltip(
                    'For security purposes, we\'re not showing the names of attendees.').props(':hide-delay="2000"').classes('text-center')

        ui.label('Note: you can only add people who are verified. '
                 'Each ticket will be sent to the holder\'s email.')

        attendee_list_container = ui.column().classes('gap-2')

        add_button = secondary_button(icon='person_add').on_click(show_add_attendee_input)

        with ui.row(wrap=False).classes('justify-center') as add_attendee_row:
            add_attendee_input = rounded_email_input()
            add_attendee_input.on('blur', hide_add_attendee_input)
            add_attendee_input.on('keydown.enter', lambda: validate_and_add_attendee())
            append = add_attendee_input.add_slot('append')
            with append:
                save_btn = primary_button(icon="save").props(
                    'round dense flat').classes(remove='min-w-32').on_click(validate_and_add_attendee)

        add_attendee_row.set_visibility(False)
        update_attendee_list()

        ui.label('Checkout').classes(
            'text-2xl font-bold')

        with ui.row(wrap=False).classes('justify-between'):
            ui.label('Total quantity:').classes('text-lg')
            quantity_label = ui.label().classes('font-bold text-lg')

        with ui.row(wrap=False).classes('justify-between pl-2') as members_row:
            ui.label('Members:')
            member_no_label = ui.label().classes('font-bold')

        with ui.row(wrap=False).classes('justify-between pl-2') as non_members_row:
            ui.label('Non-members:')
            non_member_no_label = ui.label().classes('font-bold')

        totals = {'members': 0, 'non_members': 0}
        members_row.bind_visibility_from(totals, 'members', backward=lambda a: bool(a))
        non_members_row.bind_visibility_from(
            totals, 'non_members', backward=lambda a: bool(a))

        with ui.column().classes('gap-1'):
            ui.label('Total:').classes('text-2xl')
            total_price_label = ui.label().classes('font-bold text-3xl')

        update_totals()

        ui.label("Choose your payment method:")

        app.add_static_files(url_path='/static/images/',
                             local_directory='static/images')

        with primary_button().classes("h-12") as card_pay_button:
            with ui.row(wrap=False).classes(add='gap-3 justify-center', remove='justify-between'):

                if user_agent == "ios":
                    ui.html(
                        f'<img src="/static/images/applePay.svg" class="h-full w-fit object-contain" />', sanitize=False).classes(replace='w-fit')
                ui.html(
                    f'<img src="/static/images/visa.svg" class="h-full w-auto object-contain" />', sanitize=False).classes(replace='w-fit')
                ui.html(
                    f'<img src="/static/images/mastercard.svg" class="h-full w-auto object-contain" />', sanitize=False).classes(replace='w-fit')
                ui.html(
                    f'<img src="/static/images/arca.svg" class="h-full w-auto object-contain" />', sanitize=False).classes(replace='w-fit')

        card_pay_button.on_click(
            lambda: buy_ticket(PaymentProvider.VPOS, card_pay_button))

        with primary_button('MYAMERIA', icon='img:static/images/myameria.png').classes("h-12 text-black") as myameria_button:
            myameria_button.on_click(
                lambda: buy_ticket(PaymentProvider.MYAMERIA, myameria_button))

            # if user_agent in ('ios', 'android'):
            #     with primary_button() as idram_button:
            #         ui.image("static/images/idram.png").classes('object-scale-down h-auto w-1/2')
            #         idram_button.on_click(
            #             lambda: buy_ticket(PaymentProvider.IDRAM, idram_button))

    async def existing_page():
        main_col.classes(add='gap-5 p-5')
        ui.row()
        title = ui.label().classes('text-3xl font-bold p-4')
        with ui.column():
            subtitle = ui.label().classes('text-lg')
            send_again_btn = secondary_button('Send it again').on_click(
                lambda: send_pass(person, send_again_btn))
            primary_button('Buy for others').on_click(create_main_page)

        if person.status == PersonStatus.approved:
            title.text = f"You already have a ticket for {event.name}"
            subtitle.text = f"Haven't received it?"
        elif person.status == PersonStatus.member:
            title.text = f"You can use your Membership pass to access {event.name}"
            subtitle.text = f"Can't find it?"

    async def create_main_page():
        attendees.clear()
        main_col.clear()
        with main_col:
            await main_page()

    async with frame(show_footer=False) as main_col:
        await ui.context.client.connected()
        await main_page()
