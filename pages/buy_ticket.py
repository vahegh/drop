from datetime import datetime, timezone
from nicegui import ui, app
from fastapi import Request
from httpx import HTTPStatusError
from frame import frame
from enums import PaymentProvider, PersonStatus
from api_models import PersonResponseFull, PaymentConfirmRequest
from helpers import get_user_agent
from components import (rounded_email_input, secondary_button, primary_button, toast, event_datetime_col,
                        page_header, section, positive_button, binding_card, outline_button, payment_choice)

from storage_cache import get_cache
from uuid import UUID
from services.event_ticket import get_tickets_by_person_id
from services.payment import init_payment, create_payment, confirm_payment
from services.person import get_person_by_email
from services.mailing import EmailRequest, send_email
from services.templating import generate_template
from services.vpos_payment import make_binding_payment_vpos, VposMakeBindingPaymentRequest
from dependencies import Depends, logged_in
from db_models import PaymentIntent, Payment
from services.payment_intent import create_payment_intent
from consts import APP_BASE_URL
import logging

logger = logging.getLogger(__name__)


@ui.page('/buy-ticket', title='Buy Your Ticket | Drop Dead Disco')
async def buy_ticket_page(request: Request, event_id: UUID, logged_in=Depends(logged_in)):
    if not logged_in:
        ui.navigate.to(f'/login?redirect_url=/buy-ticket?event_id={event_id}')
        return

    cache = get_cache()

    person: PersonResponseFull = request.state.person

    event = await cache.fetch_event(event_id)

    # await notify_payment_page(person)

    user_agent = await get_user_agent(request)

    attendees = [person]

    async def main_page():
        async def handle_payment():
            selected = radio.value
            if selected is None:
                ui.notify('Please select a payment method', type='warning')
                return

            amount = update_totals()
            if amount == 0:
                toast('0 AMD?')
                return

            pay_btn.props(add='loading')

            method = payment_methods[selected]
            payment_provider = method['provider']
            ticket_holders = [a.id for a in attendees]

            new_payment = await create_payment(
                Payment(
                    person_id=person.id,
                    event_id=event.id,
                    amount=amount,
                    provider=payment_provider
                )
            )

            for id in ticket_holders:
                await create_payment_intent(
                    PaymentIntent(
                        order_id=new_payment.order_id,
                        recipient_id=id
                    )
                )

            if payment_provider == PaymentProvider.BINDING:
                card_id = method['data']
                try:
                    payment_resp = await make_binding_payment_vpos(card_id, new_payment.order_id, new_payment.amount)
                except Exception as e:
                    logger.error(f"Unable to make binding payment: {str(e)}")

                else:
                    if payment_resp.PaymentID:
                        ui.navigate.to(
                            f"/bindingpayment?order_id={new_payment.order_id}&payment_id={payment_resp.PaymentID}")
                    else:
                        ui.navigate.to(
                            f"/bindingpayment?order_id={new_payment.order_id}&payment_id=None")

            else:
                try:
                    url = await init_payment(new_payment, save_card=save_tick.value)

                except HTTPStatusError as e:
                    if e.response.status_code == 409:
                        main_col.clear()
                        with main_col:
                            existing_page()
                        return
                else:
                    ui.navigate.to(url)

            pay_btn.props(remove='loading')

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
                elif p.status == PersonStatus.verified:
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

            new_attendee = await get_person_by_email(email)

            async def invite(email):
                invite_btn.props(add='loading')
                context = {
                    "inviter_name": person.full_name,
                    "inviter_first_name": person.first_name,
                    "event_name": event.name,
                    "signup_url": f"{APP_BASE_URL}/login",
                    "event_url": f"{APP_BASE_URL}/event/{event.id}"
                }

                body = await generate_template("invite.html", context=context)
                email_req = EmailRequest(
                    recipient_email=email,
                    subject="You have been invited to Drop Dead Disco",
                    body=body,
                    transactional=False
                )

                await send_email(email_req)
                invite_dl.clear()
                with invite_dl:
                    with ui.card():
                        with section("Invitation sent!"):
                            ui.markdown(
                                f"You have invited **{email}** to join Drop Dead Disco. You can buy a ticket for them after they are approved.").classes('text-center')

            if not new_attendee:
                with ui.dialog(value=True) as invite_dl:
                    with ui.card():
                        with section("This person is not registered", subtitle="Send them an invite link"):
                            invite_btn = primary_button(
                                "Send invite").on_click(lambda: invite(email))

            elif new_attendee.status not in (PersonStatus.verified, PersonStatus.member):
                toast('Can\'t buy a ticket for this person', type='warning')
            else:
                if await get_tickets_by_person_id(new_attendee.id, event.id):
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
                    with ui.card().classes('w-full items-center justify-center rounded-full').props('flat bordered'):
                        with ui.row(wrap=False).classes('gap-1') as email_row:
                            ui.label(f'{attendee.email}').classes(
                                'text-sm')
                        if attendee == person:
                            with email_row:
                                ui.label("You").classes('ml-auto text-green-700')
                        else:
                            with email_row:
                                ui.icon('close').classes('cursor-pointer ml-auto').on('click',
                                                                                      lambda a=attendee: remove_attendee(a))

        page_header(event.name)

        with section():
            event_datetime_col(event)

        with section("Attendees", subtitle="You can only add people who are verified. They'll see their ticket on their profile."):

            attendee_list_container = ui.column().classes('gap-2 w-full')
            add_button = secondary_button(icon='person_add').on_click(show_add_attendee_input)

            with ui.row(wrap=False).classes('justify-center') as add_attendee_row:
                add_attendee_input = rounded_email_input()
                add_attendee_input.on('blur', hide_add_attendee_input)
                add_attendee_input.on('keydown.enter', lambda: validate_and_add_attendee())
                append = add_attendee_input.add_slot('append')
                with append:
                    save_btn = primary_button(icon="save").props(
                        'round dense flat').on_click(validate_and_add_attendee)

        add_attendee_row.set_visibility(False)
        update_attendee_list()

        with section('Checkout'):
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

        with section():
            with ui.row(wrap=False).classes('justify-between pl-2') as non_members_row:
                ui.label('Total:').classes('text-2xl')
                total_price_label = ui.label().classes('font-bold text-3xl')

        update_totals()

        with section("Choose your payment method:"):
            card_bindings = [b for b in person.card_bindings if b.is_active]

            options = {}
            payment_methods = {}

            radio = ui.radio(options).classes(
                'w-full space-y-2 dark:bg-[#24262b]').props('left-label')

            idx = 1
            if card_bindings:
                for i, card in enumerate(card_bindings):
                    options[idx] = ""
                    payment_methods[idx] = {
                        'provider': PaymentProvider.BINDING,
                        'data': card.id
                    }

                    radio.update()
                    with ui.teleport(f'#{radio.html_id} > div:nth-child({i+1}) .q-radio__label'):
                        binding_card(card)
                    idx += 1

            options[idx] = ""
            payment_methods[idx] = {
                'provider': PaymentProvider.VPOS,
                'data': None
            }

            with ui.teleport(f'#{radio.html_id} > div:nth-child({idx}) .q-radio__label'):
                card_idx = idx
                with payment_choice():
                    ui.image("static/images/visa.svg").classes('w-10')
                    ui.image("static/images/mastercard.svg").classes('w-10')
                    ui.image("static/images/arca.svg").classes('w-10')

                save_tick = ui.checkbox("Save card details").classes('w-full justify-center').props('color=dark').bind_visibility_from(
                    radio, 'value', value=card_idx)

            radio.update()
            idx += 1

            if user_agent == "ios":
                options[idx] = ""
                payment_methods[idx] = {
                    'provider': PaymentProvider.APPLEPAY,
                    'data': None
                }
                with ui.teleport(f'#{radio.html_id} > div:nth-child({idx}) .q-radio__label'):
                    with payment_choice():
                        ui.image("static/images/applePay.svg").classes('w-10')

                radio.update()
                idx += 1

            options[idx] = ""
            payment_methods[idx] = {
                'provider': PaymentProvider.MYAMERIA,
                'data': None
            }

            with ui.teleport(f'#{radio.html_id} > div:nth-child({idx}) .q-radio__label'):
                with payment_choice():
                    ui.label('MYAMERIA')
                    ui.image('static/images/myameria.png').classes('w-6')

            radio.update()

        with section():
            pay_btn = primary_button('Pay Now').on_click(lambda: handle_payment())

    async def existing_page():
        main_col.classes(add='gap-5 p-5')
        ui.row()
        title = ui.label().classes('text-3xl font-bold p-4')
        if person.status == PersonStatus.verified:
            title.text = f"You already have a ticket for {event.name}"
        elif person.status == PersonStatus.member:
            title.text = f"You can use your Membership pass to access {event.name}"

        with ui.column():
            ui.label("You can see it in your profile").classes('text-lg')
            secondary_button('Go to your profile').on_click(lambda: ui.navigate.to('/'))
            primary_button('Buy another ticket').on_click(create_main_page)

    async def create_main_page():
        attendees.clear()
        main_col.clear()
        with main_col:
            await main_page()

    async with frame() as main_col:
        await ui.context.client.connected()
        await main_page()
