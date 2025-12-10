from datetime import datetime, timezone
from nicegui import ui, app
from collections import defaultdict
from fastapi import Request
from frame import frame
from enums import PaymentProvider, PersonStatus
from api_models import PersonResponseFull
from helpers import get_user_agent, gtag
from components import (rounded_email_input, primary_button, toast,
                        event_datetime_card, page_header, section,
                        binding_card, outline_button, payment_choice, section_title)
from storage_cache import get_cache
from uuid import UUID
from services.event_ticket import get_tickets_by_person_id
from services.payment import init_payment, create_payment
from services.person import get_person_by_email
from services.mailing import EmailRequest, send_email
from services.templating import generate_template
from services.drink import get_all_drinks
from services.vpos_payment import make_binding_payment_vpos
from dependencies import Depends, logged_in
from db_models import PaymentIntent, Payment, DrinkPaymentIntent
from services.payment_intent import create_payment_intent
from services.drink_payment_intent import create_drink_payment_intent
from services.telegram import notify_payment_page_view
from consts import APP_BASE_URL
import logging

logger = logging.getLogger(__name__)


@ui.page('/buy-ticket', title='Buy Your Ticket | Drop Dead Disco')
async def buy_ticket_page(request: Request, event_id: UUID, logged_in=Depends(logged_in)):
    if not logged_in:
        ui.navigate.to(f'/login?redirect_url=/buy-ticket?event_id={event_id}')
        return

    cache = get_cache()
    event = await cache.fetch_event(event_id)
    person: PersonResponseFull = request.state.person

    if person.status not in (PersonStatus.member, PersonStatus.verified):
        ui.navigate.to("/")
        return

    # await notify_payment_page_view(person)
    user_agent = await get_user_agent(request)

    cart = {
        'tickets': [person],
        'drinks': defaultdict(int)
    }

    async def main_page():
        nonlocal cart
        pay_btn = None
        total_price = 0

        async def handle_payment():
            selected = radio.value
            if selected is None:
                ui.notify('Please select a payment method', type='warning')
                return

            amount = update_totals()
            if amount == 0:
                toast('0 AMD?')
                return

            if pay_btn:
                pay_btn.props(add='loading')

            method = payment_methods[selected]
            payment_provider = method['provider']

            new_payment = await create_payment(
                Payment(
                    person_id=person.id,
                    event_id=event.id,
                    amount=amount,
                    provider=payment_provider
                )
            )

            if cart['tickets']:
                for attendee in cart['tickets']:
                    await create_payment_intent(
                        PaymentIntent(
                            order_id=new_payment.order_id,
                            recipient_id=attendee.id
                        )
                    )

            if cart['drinks']:
                for drink_id, qty in cart['drinks'].items():
                    for _ in range(qty):
                        await create_drink_payment_intent(
                            DrinkPaymentIntent(
                                order_id=new_payment.order_id,
                                drink_id=drink_id
                            )
                        )

            if payment_provider == PaymentProvider.BINDING:
                card_id = method['data']
                try:
                    payment_resp = await make_binding_payment_vpos(card_id, new_payment.order_id,
                                                                   new_payment.amount)
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
                except Exception as e:
                    toast(f"Unable to start payment: {str(e)}")
                else:
                    ui.navigate.to(url)

            if pay_btn:
                pay_btn.props(remove='loading')

        drinks = await get_all_drinks()

        def update_totals():
            nonlocal total_price
            ticket_price = event.general_admission_price if datetime.now(
                timezone.utc) > event.early_bird_date else event.early_bird_price
            total_price = 0

            for attendee in cart['tickets']:
                if attendee.status == PersonStatus.member:
                    total_price += event.member_ticket_price
                elif attendee.status == PersonStatus.verified:
                    total_price += ticket_price

            for drink_id, quantity in cart['drinks'].items():
                if quantity > 0:
                    drink = next((d for d in drinks if d.id == drink_id), None)
                    if drink:
                        total_price += quantity * drink.price

            cart_summary.refresh()
            return total_price

        async def validate_and_add_attendee(email_input: ui.input):
            if not email_input.validate():
                return

            email = email_input.value

            for attendee in cart['tickets']:
                if attendee.email == email:
                    ui.notify('Person already added')
                    return

            new_attendee = await get_person_by_email(email)

            if not new_attendee:
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
                    gtag("invite_friend", {"person_id": str(person.id)})

                    invite_dl.clear()
                    with invite_dl:
                        with ui.card():
                            with section("Invitation sent!"):
                                ui.markdown(
                                    f"You have invited **{email}** to join Drop Dead Disco. You can buy a ticket for them after they are approved.").classes(
                                    'text-center')

                with ui.dialog(value=True) as invite_dl:
                    with ui.card():
                        with section("This person is not registered", subtitle="Send them an invite link"):
                            invite_btn = primary_button(
                                "Send invite").on_click(lambda: invite(email))

            elif new_attendee.status not in (PersonStatus.verified, PersonStatus.member):
                toast('Can\'t buy a ticket for this person', type='warning')
            else:
                if await get_tickets_by_person_id(new_attendee.id, event.id):
                    ui.notify(f"This person already has a ticket for {event.name}.")
                    return
                else:
                    cart['tickets'].append(new_attendee)
                    attendee_list.refresh()
                    update_totals()

        page_header(event.name)

        with section():
            event_datetime_card(event)

        @ui.refreshable
        def cart_summary():
            nonlocal pay_btn
            with section("Checkout"):
                with ui.card().classes(
                        'w-full items-center border-1', remove='rounded-3xl').props('flat'):
                    ticket_price = event.general_admission_price if datetime.now(
                        timezone.utc) > event.early_bird_date else event.early_bird_price

                    for attendee in cart['tickets']:
                        price = 0
                        if attendee.status == PersonStatus.member:
                            price = event.member_ticket_price
                        elif attendee.status == PersonStatus.verified:
                            price = ticket_price

                        if price > 0:
                            with ui.row().classes('justify-between w-full'):
                                ui.label(f"Ticket | {attendee.first_name}").classes('text-sm')
                                ui.label(f"{price:,d} AMD").classes('text-sm')

                    for drink_id, quantity in cart['drinks'].items():
                        if quantity > 0:
                            drink = next((d for d in drinks if d.id == drink_id), None)
                            if drink:
                                with ui.row().classes('justify-between w-full'):
                                    ui.label(f"{drink.name} x{quantity}").classes('text-sm')
                                    ui.label(
                                        f"{drink.price * quantity:,d} AMD").classes('text-sm')

                    ui.separator()

                    with ui.row().classes('justify-between w-full px-4 pt-2'):
                        section_title('Total:')
                        section_title(f"{total_price:,d} AMD")

        @ui.refreshable
        def attendee_list():
            with section("Attendees",
                         subtitle="You can only add people who are verified. They'll see their ticket on their profile."):
                for attendee in cart['tickets']:
                    with ui.card().classes('w-full items-center justify-center rounded-full').props(
                            'flat'):
                        with ui.row(wrap=False).classes('gap-1') as email_row:
                            ui.label(f'{attendee.email}').classes('text-sm')
                            if attendee.id == person.id:
                                with email_row:
                                    ui.label("You").classes('ml-auto text-green-500')
                            else:
                                with email_row:
                                    ui.icon('close').classes('cursor-pointer ml-auto').on('click',
                                                                                          lambda a=attendee: (
                                                                                              cart[
                                                                                                  'tickets'].remove(
                                                                                                  a),
                                                                                              attendee_list.refresh(),
                                                                                              update_totals()))

                add_attendee_input = rounded_email_input()
                with add_attendee_input.add_slot('append'):
                    save_btn = ui.button(icon="save").props(
                        'round dense flat text-color="black"').on_click(
                        lambda: validate_and_add_attendee(add_attendee_input))
                add_attendee_input.on(
                    'keydown.enter', lambda: save_btn.run_method('click'))

        attendee_list()

        # with section("Drinks", subtitle="Buy drink vouchers to skip the bar line."):
        #     for drink in drinks:
        #         with ui.card().classes(
        #                 'w-full rounded-full h-[40px] py-0 justify-center items-center').props('flat'):
        #             with ui.row(wrap=False):
        #                 ui.label(f"{drink.name} - {drink.price} AMD")

        #                 def add(d, label):
        #                     cart['drinks'][d.id] += 1
        #                     label.text = str(cart['drinks'][d.id])
        #                     update_totals()

        #                 def remove(d, label):
        #                     if cart['drinks'][d.id] > 0:
        #                         cart['drinks'][d.id] -= 1
        #                         label.text = str(cart['drinks'][d.id])
        #                         update_totals()

        #                 with ui.row(wrap=False).classes(remove='w-full'):
        #                     remove_btn = ui.button(icon='remove').props(
        #                         'round flat text-color=black size="8px"')
        #                     count_label = section_title('0')
        #                     remove_btn.on_click(lambda d=drink, l=count_label: remove(d, l))
        #                     ui.button(icon='add', on_click=lambda d=drink, l=count_label: add(d, l)).props(
        #                         'round flat text-color=black size="8px"')

        with section("Payment method"):
            card_bindings = [b for b in person.card_bindings if b.is_active]
            options = {}
            payment_methods = {}
            idx = 1

            radio = ui.radio(options).classes(
                'w-full space-y-2 dark:bg-[#24262b]').props('left-label')

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
                    ui.image("/static/images/visa.svg").classes('w-10')
                    ui.image("/static/images/mastercard.svg").classes('w-10')
                    ui.image("/static/images/arca.svg").classes('w-10')

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
                        ui.image("/static/images/applePay.svg").classes('w-10')
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
                    ui.image('/static/images/myameria.png').classes('w-6')
            radio.update()

        cart_summary()
        update_totals()

        with section():
            ui.space().classes('h-[40px]')
            pay_btn = primary_button('Pay Now').classes(
                'fixed bottom-6 z-50').on_click(lambda: handle_payment())

    async with frame():
        await ui.context.client.connected()
        if await get_tickets_by_person_id(person.id, event_id):
            with ui.dialog() as dl:
                if person.status == PersonStatus.verified:
                    text = f"You already have a ticket for {event.name}"
                elif person.status == PersonStatus.member:
                    text = f"You can use your Membership pass to access {event.name}"
                with ui.card():
                    with section(text, subtitle="It's on your homepage."):
                        primary_button('Buy another ticket').on_click(dl.submit)
                        outline_button('Go to homepage', target='/')

            result = await dl
            if result:
                cart['tickets'] = []
                await main_page()
        else:
            await main_page()
