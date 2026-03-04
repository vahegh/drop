from datetime import datetime, timezone
from nicegui import ui
from collections import defaultdict
from fastapi import Request, HTTPException
from frame import frame
from enums import PaymentProvider, PersonStatus
from api_models import PersonResponseFull, PersonCreate
from helpers import get_user_agent, gtag_event, fbq_event, get_google_auth_url
from components import (rectangular_email_input, primary_button,
                        event_datetime_card, page_header, section,
                        binding_card, outline_button, payment_choice, section_title,
                        name_input, instagram_input)
from uuid import UUID
from services.event_ticket import get_tickets_by_person_id
from services.payment import init_payment, create_payment
from services.person import get_person_by_email, create_person
from services.drink import get_all_drinks
from services.vpos_payment import make_binding_payment_vpos
from services.event import get_event_info, get_next_event
from dependencies import Depends, logged_in
from db_models import PaymentIntent, Payment, DrinkPaymentIntent
from services.payment_intent import create_payment_intent
from services.drink_payment_intent import create_drink_payment_intent
import logging

logger = logging.getLogger(__name__)


def get_ticket_info(person, event) -> tuple[str, int]:
    if person.status == PersonStatus.member:
        return "ticket_member", event.member_ticket_price
    if datetime.now(timezone.utc) > event.early_bird_date:
        return "ticket_standard", event.general_admission_price
    return "ticket_early_bird", event.early_bird_price


def binding_card_row(b):
    from components import get_card_type
    card_type = get_card_type(b.masked_card_number[:6])
    with ui.row(wrap=False).classes('items-center gap-3 w-full'):
        if card_type == 'visa':
            ui.image('/static/images/visa.svg').classes('w-8')
        elif card_type == 'mastercard':
            ui.image('/static/images/mastercard.svg').classes('w-8')
        else:
            ui.icon('credit_card').classes('text-xl')
        ui.label(
            f"{card_type.capitalize()} •••• {b.masked_card_number[-4:]}").classes('text-sm flex-1')
        exp_m = b.card_expiry_date[-2:]
        exp_y = b.card_expiry_date[2:4]
        ui.label(f"{exp_m}/{exp_y}").classes('text-sm text-gray-400')


SELECTED_STYLE = 'border-2'


@ui.page('/buy-ticket', title='Buy Your Ticket | Drop Dead Disco', response_timeout=10)
async def buy_ticket_page(request: Request, event_id: UUID = None, logged_in=Depends(logged_in)):
    if not event_id:
        event = await get_next_event()
        if event:
            ui.navigate.to(f"/buy-ticket?event_id={event.id}")
            return
        ui.navigate.to("/")
        return

    event = await get_event_info(event_id)
    if not event:
        raise HTTPException(404, "No such event")

    user_agent = await get_user_agent(request)
    person: PersonResponseFull = request.state.person if logged_in else None

    if logged_in and person.status == PersonStatus.rejected:
        ui.navigate.to("/")
        return

    ui.add_css(f'''
        body::before {{
            content: '';
            position: fixed;
            inset: 0;
            background-image: url('{event.image_url}');
            background-size: cover;
            background-position: center;
            filter: blur(12px) brightness(25%);
            transform: scale(1.05);
            z-index: -1;
        }}
    ''')

    cart = {
        'tickets': [],
        'drinks': defaultdict(int),
    }

    drinks = await get_all_drinks()
    total_price = 0
    selected_method = None
    selected_card_el = None
    pay_btn = None

    def add_to_cart(p):
        cart['tickets'].append(p)
        ticket_id, price = get_ticket_info(p, event)
        gtag_event("add_to_cart", {"items": [{"item_id": ticket_id, "price": price}]})
        fbq_event("AddToCart")

    def remove_from_cart(p):
        cart['tickets'].remove(p)
        ticket_id, price = get_ticket_info(p, event)
        gtag_event("remove_from_cart", {"items": [{"item_id": ticket_id, "price": price}]})

    def select_method(method, card_el):
        nonlocal selected_method, selected_card_el
        if selected_card_el:
            selected_card_el.classes(remove=SELECTED_STYLE)
        selected_method = method
        selected_card_el = card_el
        card_el.classes(add=SELECTED_STYLE)

    async def execute_payment(payment_provider, card_id, save_card: bool):
        new_payment = await create_payment(
            Payment(
                person_id=person.id,
                event_id=event.id,
                amount=total_price,
                provider=payment_provider,
            )
        )

        items = []
        for attendee in cart['tickets']:
            await create_payment_intent(
                PaymentIntent(order_id=new_payment.order_id, recipient_id=attendee.id)
            )
            ticket_id, price = get_ticket_info(attendee, event)
            items.append({"item_id": ticket_id, "price": price})

        for drink_id, qty in cart['drinks'].items():
            for _ in range(qty):
                await create_drink_payment_intent(
                    DrinkPaymentIntent(order_id=new_payment.order_id, drink_id=drink_id)
                )

        gtag_event("begin_checkout", {"currency": "AMD",
                   "value": new_payment.amount, "items": items})
        fbq_event("InitiateCheckout")

        if payment_provider == PaymentProvider.BINDING:
            try:
                resp = await make_binding_payment_vpos(card_id, new_payment.order_id, new_payment.amount)
            except Exception as e:
                logger.error(f"Unable to make binding payment: {e}")
                pay_btn.props(remove='loading')
                pay_btn.enable()
                return
            payment_id = resp.PaymentID or "None"
            ui.navigate.to(
                f"/bindingpayment?order_id={new_payment.order_id}&payment_id={payment_id}")
        else:
            try:
                url = await init_payment(new_payment, save_card=save_card)
            except Exception as e:
                ui.notify(f"Unable to start payment: {e}", type='warning')
                pay_btn.props(remove='loading')
                pay_btn.enable()
                return
            ui.navigate.to(url)

    @ui.refreshable
    def cart_summary():
        with section("Checkout"):
            with ui.card().classes('w-full items-center border-2 bg-transparent', remove='rounded-3xl').props('flat'):
                for attendee in cart['tickets']:
                    _, price = get_ticket_info(attendee, event)
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
                                ui.label(f"{drink.price * quantity:,d} AMD").classes('text-sm')

                ui.separator()
                with ui.row().classes('justify-between w-full px-4 pt-2'):
                    section_title('Total:')
                    section_title(f"{total_price:,d} AMD")

    def update_totals():
        nonlocal total_price
        total_price = 0
        for attendee in cart['tickets']:
            _, price = get_ticket_info(attendee, event)
            total_price += price
        for drink_id, qty in cart['drinks'].items():
            drink = next((d for d in drinks if d.id == drink_id), None)
            if drink and qty > 0:
                total_price += qty * drink.price
        cart_summary.refresh()
        if pay_btn:
            if total_price > 0:
                pay_btn.enable()
                pay_btn.set_text(f"Pay {total_price:,d} AMD")
            else:
                pay_btn.disable()
                pay_btn.set_text("Pay Now")

    async def check_guest_email():
        if not guest_email_inp.validate():
            return
        check_btn.props(add='loading disable')
        existing = await get_person_by_email(guest_email_inp.value.strip())
        if existing and existing.status in (PersonStatus.verified, PersonStatus.member):
            redirect_url = f"{request.url.path}?{request.url.query}"
            ui.navigate.to(await get_google_auth_url(redirect_url, guest_email_inp.value.strip()))
            return
        guest_extra_fields.set_visibility(True)
        check_btn.set_visibility(False)
        check_btn.props(remove='loading disable')

    async def handle_payment(save_card=False):
        nonlocal person

        if selected_method is None:
            ui.notify('Please select a payment method', type='warning')
            return
        if total_price == 0:
            ui.notify('0 AMD?', type='warning')
            return

        if not logged_in:
            if not guest_email_inp.validate():
                return
            if not guest_extra_fields.visible:
                await check_guest_email()
                return
            if not all([guest_fn_inp.validate(), guest_ln_inp.validate(), guest_insta_inp.validate()]):
                return
            if not verification_tick.value:
                ui.notify("Please accept the verification requirement to continue.", type="warning")
                return

            new_person = await create_person(PersonCreate(
                first_name=guest_fn_inp.value.strip(),
                last_name=guest_ln_inp.value.strip(),
                email=guest_email_inp.value.strip(),
                instagram_handle=guest_insta_inp.value.strip().lstrip('@'),
            ))
            if not new_person:
                ui.notify('Registration failed. Please try again later.', type='warning')
                return

            person = new_person
            add_to_cart(person)
            update_totals()
            gtag_event("sign_up", {"method": "guest_checkout"})

        if selected_method['provider'] == PaymentProvider.VPOS and logged_in:
            save_card_dl.open()
            return

        pay_btn.props(add='loading')
        pay_btn.disable()
        await execute_payment(selected_method['provider'], selected_method.get('data'), save_card)

    async def validate_and_add_attendee(email_input: ui.input):
        if not email_input.validate():
            return
        email = email_input.value
        if any(a.email == email for a in cart['tickets']):
            ui.notify('Person already added')
            return

        save_btn.props(add='loading disable')
        new_attendee = await get_person_by_email(email)

        if not new_attendee:
            refer_dl.clear()
            with refer_dl:
                with ui.card():
                    with section("Refer a friend", subtitle=""):
                        with ui.column().classes('w-full gap-0'):
                            r_email = rectangular_email_input(value=email)
                            with ui.row(wrap=False):
                                r_fn = name_input("First name", "John")
                                r_ln = name_input("Last name", "Doe")
                            r_insta = instagram_input()

                            async def submit():
                                if not all([r_fn.validate(), r_ln.validate(),
                                            r_email.validate(), r_insta.validate()]):
                                    return
                                submit_btn.props(add='loading disable')
                                new_person = await create_person(PersonCreate(
                                    first_name=r_fn.value.strip(),
                                    last_name=r_ln.value.strip(),
                                    email=r_email.value.strip(),
                                    instagram_handle=r_insta.value.strip().lstrip('@'),
                                    referer_id=person.id,
                                ))
                                if new_person:
                                    add_to_cart(new_person)
                                    gtag_event("refer_friend", {"person_id": str(person.id)})
                                    attendee_list.refresh()
                                    update_totals()
                                    refer_dl.close()
                                    add_attendee_dl.close()
                                    ui.notify(
                                        f"Successfully registered {r_email.value}", type='positive')
                                else:
                                    ui.notify("Unknown error. Please try again later.",
                                              type='warning')
                                    submit_btn.props(remove='loading disable')

                            submit_btn = primary_button('Submit').on_click(submit)
            refer_dl.open()

        elif new_attendee.status == PersonStatus.rejected:
            ui.notify("Can't buy a ticket for this person", type='warning')
        else:
            if await get_tickets_by_person_id(new_attendee.id, event.id):
                ui.notify(f"This person already has a ticket for {event.name}.")
            else:
                add_to_cart(new_attendee)
                attendee_list.refresh()
                update_totals()
                add_attendee_dl.close()

        save_btn.props(remove='loading disable')

    async with frame():
        page_header(event.name)

        with section():
            event_datetime_card(event)

        already_has_ticket = logged_in and await get_tickets_by_person_id(person.id, event_id)

        if already_has_ticket:
            banner_text = (
                f"You can use your Membership pass to access {event.name}"
                if person.status == PersonStatus.member
                else f"You already have a ticket for {event.name}"
            )
            with ui.dialog(value=True) as ticket_dl:
                with ui.card():
                    with section(banner_text, subtitle="It's on your homepage."):
                        primary_button('Buy another ticket').on_click(ticket_dl.close)
                        outline_button('Go to homepage', target='/')

        if not logged_in:
            with section("Your email", subtitle="Enter your verified email to get your ticket."):
                with ui.column().classes('gap-0 w-full'):
                    guest_email_inp = rectangular_email_input()
                    check_btn = outline_button("Check").on_click(check_guest_email)
                    guest_email_inp.on('keydown.enter', lambda: check_btn.run_method('click'))

                    with ui.column().classes('gap-0 w-full') as guest_extra_fields:
                        with ui.row(wrap=False):
                            guest_fn_inp = name_input("First name", "John")
                            guest_ln_inp = name_input("Last name", "Doe")
                        guest_insta_inp = instagram_input()
                        verification_tick = ui.checkbox(
                            f"I understand my ticket will be sent to me after "
                            f"verification. If not verified, my payment will be refunded."
                        ).props('color=dark')
                    guest_extra_fields.set_visibility(False)

        if logged_in:
            with ui.dialog() as add_attendee_dl:
                with ui.card():
                    with section("Add a friend",
                                 subtitle="You can buy tickets for registered people or refer new people."):
                        add_attendee_input = rectangular_email_input()
                        save_btn = primary_button("Add").on_click(
                            lambda: validate_and_add_attendee(add_attendee_input)
                        )
                        add_attendee_input.on('keydown.enter', lambda: save_btn.run_method('click'))

            refer_dl = ui.dialog()

            @ui.refreshable
            def attendee_list():
                with section("Attendees",
                             subtitle="Enter a friend's email to buy them a ticket."):
                    for attendee in cart['tickets']:
                        with ui.card().classes('w-full items-center justify-center rounded-full').props('flat'):
                            with ui.row(wrap=False).classes('gap-1'):
                                ui.label(attendee.email).classes('text-sm')
                                if attendee.id == person.id:
                                    ui.label("You").classes('ml-auto text-green-500')
                                else:
                                    ui.icon('close').classes('cursor-pointer ml-auto').on(
                                        'click',
                                        lambda a=attendee: (
                                            remove_from_cart(a),
                                            attendee_list.refresh(),
                                            update_totals(),
                                        ),
                                    )
                    outline_button("Add a friend", icon='cruelty_free').on_click(
                        add_attendee_dl.open)

            attendee_list()

        with ui.dialog() as save_card_dl:
            with ui.card():
                with section("Save card?",
                             subtitle="Save your card details for faster checkout next time."):
                    with ui.row().classes('w-full gap-2'):

                        async def pay_no_save():
                            save_card_dl.close()
                            pay_btn.props(add='loading')
                            pay_btn.disable()
                            await execute_payment(PaymentProvider.VPOS, None, save_card=False)

                        async def pay_and_save():
                            save_card_dl.close()
                            pay_btn.props(add='loading')
                            pay_btn.disable()
                            await execute_payment(PaymentProvider.VPOS, None, save_card=True)

                        primary_button("Save").on_click(lambda: pay_and_save())
                        outline_button("No").on_click(lambda: pay_no_save())

        with section("Payment method"):
            active_bindings = [b for b in person.card_bindings if b.is_active] if logged_in else []

            for b in active_bindings:
                method = {'provider': PaymentProvider.BINDING, 'data': b.id}
                btn = outline_button()
                with btn:
                    binding_card_row(b)
                btn.on('click', lambda m=method, el=btn: select_method(m, el))

            vpos_method = {'provider': PaymentProvider.VPOS}
            vpos_btn = outline_button()
            with vpos_btn:
                with payment_choice():
                    for img in ['visa', 'mastercard', 'arca']:
                        ui.image(f"/static/images/{img}.svg").classes('w-8')
            vpos_btn.on('click', lambda: select_method(vpos_method, vpos_btn))

            if user_agent == "ios":
                applepay_method = {'provider': PaymentProvider.APPLEPAY}
                applepay_btn = outline_button()
                with applepay_btn:
                    with payment_choice():
                        ui.image("/static/images/applePay.svg").classes('w-12')
                applepay_btn.on('click', lambda: select_method(applepay_method, applepay_btn))

            myameria_method = {'provider': PaymentProvider.MYAMERIA}
            myameria_btn = outline_button()
            with myameria_btn:
                with payment_choice():
                    ui.label('MyAmeria').classes('font-medium')
                    ui.image('/static/images/myameria.png').classes('w-6')
            myameria_btn.on('click', lambda: select_method(myameria_method, myameria_btn))

        cart_summary()

        ui.space().classes('h-14')
        with section() as s:
            s.classes('fixed bottom-4 z-50 px-2')
            pay_btn = primary_button("Pay Now").on_click(
                lambda: handle_payment()).classes('h-20 text-lg')

        if logged_in and not already_has_ticket:
            add_to_cart(person)
        update_totals()
