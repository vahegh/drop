from nicegui import ui
from fastapi import HTTPException, Request
from typing import Literal, Optional
from frame import frame
from components import section_title, outline_button, section
from enums import PaymentProvider, PaymentStatus
from api_models import PaymentConfirmRequest, VerifyPersonRequest, PersonResponseFull, CardBindingCreate
from uuid import UUID
import logging
from services.payment import confirm_payment
from services.vpos_payment import get_payment_details_vpos, get_card_binding_vpos
from services.card_binding import create_card_binding
from services.payment_intent import get_payment_intents
from services.event import get_event_info
from services.person import get_person
from dependencies import Depends, logged_in
from helpers import gtag_event, fbq_event
from enums import PersonStatus
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

myameria_payment_status = Literal['success', 'failure']


async def callback_page(confirm_request):
    async with frame() as main_col:
        main_col.classes('h-[100svh] px-4')
        await ui.context.client.connected()
        with section():
            status_label = section_title("Confirming your payment")
            desc_label = ui.label('Please wait...')

        with section():
            status_icon = ui.icon('check', size='100px').classes(
                'text-green-500')
            status_icon.set_visibility(False)
            sp = ui.spinner(size='100px', thickness=2)

        try:
            confirm_response = await confirm_payment(confirm_request)
        except HTTPException as e:
            sp.set_visibility(False)
            status_icon.set_visibility(True)

            if e.status_code == 409:
                status_icon.set_name('credit_score')
                status_icon.classes(replace='')
                status_label.text = "This payment is already processed."
                desc_label.text = "Your ticket should be visible on your homepage. If it isn't, please contact us via Instagram or email."
            else:
                logger.error(str(e))
                status_icon.set_name('close')
                status_icon.classes(replace='text-red-500')
                status_label.text = "Unable to process payment."
                desc_label.text = "Please check your homepage for your ticket. If it's not there, please contact us via Instagram or email."

            outline_button("Home", target='/')
            return main_col

        sp.set_visibility(False)
        status_icon.set_visibility(True)

        if confirm_response.status == PaymentStatus.CONFIRMED:
            status_label.text = "Payment succesful!"
            desc_label.text = "Each recipient can see their ticket on their profile. If you are waiting to be verified, you'll get your ticket immediately after verification. If your application isn't accepted, you'll receive a refund."
            outline_button("Event Information", target=f"/event/{confirm_response.event_id}")

            intents = await get_payment_intents(confirm_response.order_id)
            items = []
            event = await get_event_info(confirm_response.event_id)
            for i in intents:
                person = await get_person(i.recipient_id)
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

                items.append(
                    {
                        "item_id": id,
                        "price": price
                    }
                )

            gtag_event(
                "purchase",
                {
                    "currency": "AMD",
                    "value": confirm_response.amount,
                    "transaction_id": str(confirm_response.order_id),
                    "items": items
                }
            )
            fbq_event("Purchase", params={"value": float(
                confirm_response.amount), "currency": "AMD"})

        else:
            status_icon.set_name('close')
            status_icon.classes(replace='text-red-500')
            status_label.text = "Payment Failed"
            desc_label.text = confirm_response.description if confirm_response.description else ""

    return main_col


@ui.page('/ameriatransactionstate', title='Payment Confirmation | Drop Dead Disco')
async def myameria_callback(transactionId: int, paymentId: UUID, status=myameria_payment_status, errorMessage: Optional[str] = None):
    if not transactionId or not paymentId or not status:
        raise HTTPException(404)

    confirm_request = PaymentConfirmRequest(
        order_id=int(transactionId),
        provider=PaymentProvider.MYAMERIA,
        payment_id=paymentId
    )

    await callback_page(confirm_request)


@ui.page('/vpostransactionstate', title='Payment Confirmation | Drop Dead Disco')
async def vpos_callback(request: Request, orderID: int, resposneCode: str, paymentID: UUID, opaque: Optional[str] = None, description: Optional[str] = None):
    if not orderID or not resposneCode or not paymentID:
        raise HTTPException(404)

    if opaque:
        person: PersonResponseFull = request.state.person
        card_binding_vpos = await get_card_binding_vpos(opaque)

        try:
            await create_card_binding(
                CardBindingCreate(
                    id=opaque,
                    person_id=person.id,
                    masked_card_number=card_binding_vpos.CardPan,
                    card_expiry_date=card_binding_vpos.ExpDate,
                    is_active=card_binding_vpos.IsAvtive
                )
            )
            fbq_event("AddPaymentInfo")
        except Exception as e:
            logger.error(f"Unable to add card binding: {str(e)}")

    confirm_request = PaymentConfirmRequest(
        order_id=int(orderID),
        provider=PaymentProvider.VPOS,
        payment_id=paymentID
    )

    await callback_page(confirm_request)


@ui.page('/cardbinding', title='Add Payment Method | Drop Dead Disco')
async def card_binding_callback(request: Request, orderID: int, resposneCode: str, paymentID: UUID, opaque: Optional[str] = None, description: Optional[str] = None, logged_in=Depends(logged_in)):
    if not orderID or not resposneCode or not paymentID:
        raise HTTPException(404)

    if not logged_in:
        raise HTTPException(401)

    person: PersonResponseFull = request.state.person

    payment_details = await get_payment_details_vpos(paymentID)

    if payment_details.ResponseCode == "00":
        card_binding_vpos = await get_card_binding_vpos(opaque)

        if not card_binding_vpos:
            ui.label("Unable to attach card")

        try:
            await create_card_binding(
                CardBindingCreate(
                    id=opaque,
                    person_id=person.id,
                    masked_card_number=card_binding_vpos.CardPan,
                    card_expiry_date=card_binding_vpos.ExpDate,
                    is_active=card_binding_vpos.IsAvtive
                )
            )
            fbq_event("AddPaymentInfo")
            ui.navigate.to("/profile")
        except Exception as e:
            logger.warning(f"Unable to create card binding: {str(e)}")


@ui.page('/bindingpayment', title='Payment Confirmation | Drop Dead Disco', response_timeout=100)
async def binding_payment_callback(request: Request, order_id, payment_id):
    confirm_request = PaymentConfirmRequest(
        order_id=int(order_id),
        provider=PaymentProvider.BINDING,
        payment_id=payment_id
    )

    await callback_page(confirm_request)
