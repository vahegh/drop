from datetime import datetime, timezone
from nicegui import ui
from collections import defaultdict
from fastapi import Request
from frame import frame
from enums import PaymentProvider, PersonStatus
from api_models import PersonResponseFull, PersonCreate
from helpers import get_user_agent, gtag_event, fbq_event
from components import (rectangular_email_input, primary_button,
                        event_datetime_card, page_header, section,
                        binding_card, outline_button, payment_choice, section_title,
                        name_input, instagram_input, outline_google_button)
from uuid import UUID
from services.event_ticket import get_tickets_by_person_id
from services.payment import init_payment, create_payment
from services.person import get_person_by_email
from services.mailing import EmailRequest, send_email
from services.templating import generate_template
from services.drink import get_all_drinks
from services.vpos_payment import make_binding_payment_vpos
from services.event import get_event_info
from routes.attendance import get_attendance
from routes.auth import register
from dependencies import Depends, logged_in
from db_models import PaymentIntent, Payment, DrinkPaymentIntent
from services.payment_intent import create_payment_intent
from services.drink_payment_intent import create_drink_payment_intent
from consts import APP_BASE_URL
import logging

logger = logging.getLogger(__name__)


@ui.page('/buy-ticket', title='Buy Your Ticket | Drop Dead Disco', response_timeout=10)
async def buy_ticket_page(request: Request, event_id: UUID, logged_in=Depends(logged_in)):
    event = await get_event_info(event_id)
    user_agent = await get_user_agent(request)

    person: PersonResponseFull = request.state.person if logged_in else None

    if logged_in and person.status not in (PersonStatus.member, PersonStatus.verified):
        ui.navigate.to("/")
        return

    cart = {
        'tickets': [],
        'drinks': defaultdict(int)
    }

    def add_to_cart(person):
        cart['tickets'].append(person)
        if person.status == PersonStatus.member:
            id = "ticket_member"
            price = event.member_ticket_price

        elif person.status == PersonStatus.verified:
            if datetime.now(timezone.utc) > event.early_bird_date:
                id = "ticket_standard"
                price = event.general_admission_price

            else:
                id = "ticket_early_bird"
                price = event.early_bird_price

        gtag_event("add_to_cart", {"items": [{
            "item_id": id,
            "price": price
        }]})
        fbq_event("AddToCart")
        print(f"added {person.first_name} to cart")

    def remove_from_cart(person):
        cart['tickets'].remove(person)
        if person.status == PersonStatus.member:
            id = "ticket_member"
            price = event.member_ticket_price

        elif person.status == PersonStatus.verified:
            if datetime.now(timezone.utc) > event.early_bird_date:
                id = "ticket_standard"
                price = event.general_admission_price

            else:
                id = "ticket_early_bird"
                price = event.early_bird_price

        gtag_event("remove_from_cart", {"items": [{
            "item_id": id,
            "price": price
        }]})
        print(f"removed {person.first_name} from cart")

    async def main_page():
        pay_btn = None
        total_price = 0

        # Dialog for guest registration
        guest_dialog = ui.dialog()

        async def handle_payment():
            selected = radio.value
            if selected is None:
                ui.notify('Please select a payment method', type='warning')
                return

            if total_price == 0:
                ui.notify('0 AMD?', type='warning')
                return

            if not logged_in:
                guest_dialog.open()
                return

            if pay_btn:
                pay_btn.props(add='loading')

            method = payment_methods[selected]
            payment_provider = method['provider']

            new_payment = await create_payment(
                Payment(
                    person_id=person.id,
                    event_id=event.id,
                    amount=total_price,
                    provider=payment_provider
                )
            )

            items = []
            if cart['tickets']:
                for attendee in cart['tickets']:
                    await create_payment_intent(
                        PaymentIntent(
                            order_id=new_payment.order_id,
                            recipient_id=attendee.id
                        )
                    )
                    if attendee.status == PersonStatus.member:
                        id = "ticket_member"
                        price = event.member_ticket_price

                    elif attendee.status == PersonStatus.verified:
                        if datetime.now(timezone.utc) > event.early_bird_date:
                            id = "ticket_standard"
                            price = event.general_admission_price

                        else:
                            id = "ticket_early_bird"
                            price = event.early_bird_price

                    items.append(
                        {
                            "item_id": id,
                            "price": price
                        }
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

            gtag_event("begin_checkout", {"currency": "AMD",
                                          "value": new_payment.amount, "items": items})
            fbq_event("InitiateCheckout")

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
                    url = await init_payment(new_payment, save_card=save_tick.value if logged_in else False)
                except Exception as e:
                    ui.notify(f"Unable to start payment: {str(e)}", type='warning')
                else:
                    ui.navigate.to(url)

            if pay_btn:
                pay_btn.props(remove='loading')

        async def handle_guest_payment():
            nonlocal person

            if not all([
                guest_fn_inp.validate(),
                guest_ln_inp.validate(),
                guest_email_inp.validate(),
                guest_insta_inp.validate(),
            ]):
                return

            if not verification_tick.value:
                ui.notify("Please accept the verification requirement to continue.", type="warning")
                return

            continue_btn.props(add='loading disable')

            first_name = guest_fn_inp.value.strip()
            last_name = guest_ln_inp.value.strip()
            email = guest_email_inp.value.strip()
            insta = guest_insta_inp.value.strip().lstrip('@')

            payload = PersonCreate(
                first_name=first_name,
                last_name=last_name,
                email=email,
                instagram_handle=insta
            )

            new_person = await register(payload)

            if not new_person:
                ui.notify('Registration failed. Please try again.', type='warning')
                continue_btn.props(remove='loading disable')
                return

            person = new_person
            gtag_event("sign_up", {"method": "guest_checkout"})

            guest_dialog.close()

            if pay_btn:
                pay_btn.props(add='loading')

            selected = radio.value
            method = payment_methods[selected]
            payment_provider = method['provider']

            new_payment = await create_payment(
                Payment(
                    person_id=person.id,
                    event_id=event.id,
                    amount=total_price,
                    provider=payment_provider
                )
            )

            items = []
            ticket_price = event.general_admission_price if datetime.now(
                timezone.utc) > event.early_bird_date else event.early_bird_price

            await create_payment_intent(
                PaymentIntent(
                    order_id=new_payment.order_id,
                    recipient_id=person.id
                )
            )

            if datetime.now(timezone.utc) > event.early_bird_date:
                id = "ticket_standard"
                price = event.general_admission_price
            else:
                id = "ticket_early_bird"
                price = event.early_bird_price

            items.append({
                "item_id": id,
                "price": price
            })

            if cart['drinks']:
                for drink_id, qty in cart['drinks'].items():
                    for _ in range(qty):
                        await create_drink_payment_intent(
                            DrinkPaymentIntent(
                                order_id=new_payment.order_id,
                                drink_id=drink_id
                            )
                        )

            gtag_event("begin_checkout", {"currency": "AMD",
                                          "value": new_payment.amount, "items": items})
            fbq_event("InitiateCheckout")

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
                    url = await init_payment(new_payment, save_card=False)
                except Exception as e:
                    ui.notify(f"Unable to start payment: {str(e)}", type='warning')
                else:
                    ui.navigate.to(url)

            if pay_btn:
                pay_btn.props(remove='loading')

            continue_btn.props(remove='loading disable')

        async def check_guest_email():
            if not guest_email_inp.validate():
                return

            email = guest_email_inp.value.strip()
            check_btn.props(add='loading disable')

            existing_person = await get_person_by_email(email)

            if existing_person and existing_person.status in (PersonStatus.verified, PersonStatus.member):
                guest_dialog.close()
                ui.navigate.to(f'/login?redirect_url=/buy-ticket?event_id={event_id}')
                return
            else:
                guest_additional_fields.set_visibility(True)
                check_section.set_visibility(False)
                continue_section.set_visibility(True)

            check_btn.props(remove='loading disable')

        with guest_dialog:
            with ui.card():
                with section("Your details", subtitle="Enter your details to buy your ticket"):
                    with ui.column().classes('gap-0 w-full'):
                        guest_email_inp = rectangular_email_input()
                        with ui.column().classes('gap-0 w-full') as guest_additional_fields:
                            with ui.row(wrap=False):
                                guest_fn_inp = name_input("First name", "John")
                                guest_ln_inp = name_input("Last name", "Doe")
                            guest_insta_inp = instagram_input()
                            verification_tick = ui.checkbox(
                                f"You acknowledge that your ticket for {event.name} will be sent after verification. If you're not verified, your ticket will be refunded.").props('color=dark')
                        guest_additional_fields.set_visibility(False)

                    with ui.column().classes('w-full items-center') as check_section:
                        check_btn = primary_button("Continue").on_click(check_guest_email)
                        ui.label("OR")
                        outline_google_button("Sign in with Google",
                                              url=f"/buy-ticket?event_id={event_id}")
                        guest_email_inp.on('keydown.enter', lambda: check_btn.run_method('click'))

                    with ui.column().classes('w-full') as continue_section:
                        continue_btn = primary_button(
                            "Continue to Payment").on_click(handle_guest_payment)
                    continue_section.set_visibility(False)

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

            if not logged_in:
                total_price = ticket_price

            for drink_id, quantity in cart['drinks'].items():
                if quantity > 0:
                    drink = next((d for d in drinks if d.id == drink_id), None)
                    if drink:
                        total_price += quantity * drink.price

            cart_summary.refresh()
            btn_text = f"Pay {total_price} AMD" if total_price > 0 else "Pay now"
            pay_btn.set_text(btn_text)

            return total_price

        async def validate_and_add_attendee(email_input: ui.input):
            if not email_input.validate():
                return

            email = email_input.value

            for attendee in cart['tickets']:
                if attendee.email == email:
                    ui.notify('Person already added')
                    return

            save_btn.props(add='loading disable')

            new_attendee = await get_person_by_email(email)

            if not new_attendee:
                async def invite(email):
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
                    gtag_event("invite_friend", {"person_id": str(person.id)})

                    add_attendee_dl.clear()
                    with add_attendee_dl:
                        with ui.card():
                            with section("Invitation sent!"):
                                ui.markdown(
                                    f"You have invited **{email}** to join Drop Dead Disco. You can buy a ticket for them after they are approved.").classes(
                                    'text-center')

                async def refer_person(email):
                    add_attendee_dl.clear()
                    with add_attendee_dl:
                        with ui.card():
                            with section("Refer a friend", subtitle="They will be auto-approved on your behalf."):
                                with ui.column().classes('w-full gap-0'):
                                    email_inp = rectangular_email_input(value=email)
                                    with ui.row(wrap=False):
                                        fn_inp = name_input("First name", "John")
                                        ln_inp = name_input("Last name", "Doe")
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

                        payload = PersonCreate(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            instagram_handle=insta,
                            referer_id=person.id
                        )

                        new_person = await register(payload)

                        if new_person:
                            add_to_cart(new_person)
                            gtag_event("refer_friend", {"person_id": str(person.id)})
                            attendee_list.refresh()
                            update_totals()
                            add_attendee_dl.close()

                        else:
                            add_attendee_dl.clear()
                            with add_attendee_dl:
                                with section("Unknown error occured.", subtitle="Please try again a little later."):
                                    primary_button("Back").on_click(add_attendee_dl.close)

                    submit_btn.on_click(lambda: submit())

                person_attendance = await get_attendance(person.id)
                if person_attendance >= 2 or person.status is PersonStatus.member:
                    await refer_person(email)
                else:
                    await invite(email)

            elif new_attendee.status not in (PersonStatus.verified, PersonStatus.member):
                ui.notify('Can\'t buy a ticket for this person', type='warning')
            else:
                if await get_tickets_by_person_id(new_attendee.id, event.id):
                    ui.notify(f"This person already has a ticket for {event.name}.")
                else:
                    add_to_cart(new_attendee)
                    attendee_list.refresh()
                    update_totals()
                    add_attendee_dl.close()
            save_btn.props(remove='loading disable')
            return

        page_header(event.name)

        with section():
            event_datetime_card(event)

        @ui.refreshable
        def cart_summary():
            with section("Checkout"):
                with ui.card().classes(
                        'w-full items-center border-1', remove='rounded-3xl').props('flat'):
                    ticket_price = event.general_admission_price if datetime.now(
                        timezone.utc) > event.early_bird_date else event.early_bird_price

                    if not logged_in:
                        with ui.row().classes('justify-between w-full'):
                            ui.label("Ticket").classes('text-sm')
                            ui.label(f"{ticket_price:,d} AMD").classes('text-sm')
                    else:
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

        if logged_in:
            with ui.dialog() as add_attendee_dl:
                with ui.card():
                    with section("Add a friend", subtitle="If you have attended two or more Drop events, you can refer a friend to join us. They will be auto-approved on your behalf."):
                        add_attendee_input = rectangular_email_input()
                        save_btn = primary_button("Add").on_click(
                            lambda: validate_and_add_attendee(add_attendee_input))
                        add_attendee_input.on(
                            'keydown.enter', lambda: save_btn.run_method('click'))

            @ui.refreshable
            def attendee_list():
                with section("Attendees",
                             subtitle="Enter a friend's email to buy them a ticket. They'll see it on their homepage."):
                    def remove_attendee(attendee):
                        remove_from_cart(attendee)
                        attendee_list.refresh()
                        update_totals()

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
                                                                                              lambda a=attendee: remove_attendee(a))

                    outline_button("Add a friend", icon='cruelty_free').on_click(
                        add_attendee_dl.open)

            attendee_list()

        with section("Payment method"):
            if logged_in:
                card_bindings = [b for b in person.card_bindings if b.is_active]
            else:
                card_bindings = []

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

                if logged_in:
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

        with section():
            ui.space().classes('h-[40px]')
            with section() as s:
                s.classes('fixed bottom-6 z-50')
                pay_btn = primary_button().on_click(lambda: handle_payment())

        update_totals()

    async with frame():
        if logged_in and await get_tickets_by_person_id(person.id, event_id):
            with ui.dialog(value=True) as dl:
                if person.status == PersonStatus.verified:
                    text = f"You already have a ticket for {event.name}"
                elif person.status == PersonStatus.member:
                    text = f"You can use your Membership pass to access {event.name}"
                with ui.card():
                    with section(text, subtitle="It's on your homepage."):
                        primary_button('Buy another ticket').on_click(dl.close)
                        outline_button('Go to homepage', target='/')
            await main_page()

        else:
            if logged_in:
                add_to_cart(person)
            await main_page()
