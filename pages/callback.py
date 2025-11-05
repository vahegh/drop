from nicegui import ui, Client
from fastapi import HTTPException
from typing import Literal, Optional
from frame import frame
from elements import section_title, secondary_button
from enums import PaymentProvider, PaymentStatus
from api_models import PaymentConfirmRequest, VerifyPersonRequest
from uuid import UUID
import logging
from httpx import HTTPStatusError


logger = logging.getLogger(__name__)

myameria_payment_status = Literal['success', 'failure']


async def callback_page(confirm_request):
    async with frame(show_footer=False) as f:
        with ui.column().classes('fixed inset-0 h-full w-full'):
            status_icon = ui.icon('check', size='100px').classes(
                'text-green-500')
            status_icon.set_visibility(False)
            sp = ui.spinner(size='100px', thickness=2)

        with ui.column().classes('h-[90vh] gap-8 p-8 justify-between', remove='justify-center'):
            with ui.column():
                status_label = section_title("Confirming your payment")
                desc_label = ui.label('Please wait...')

            try:
                confirm_response = await client.confirm_payment(confirm_request)
            except HTTPStatusError as e:
                sp.set_visibility(False)
                status_icon.set_visibility(True)

                if e.response.status_code == 409:
                    status_icon.set_name('credit_score')
                    status_icon.classes(replace='')
                    status_label.text = "This payment is already processed."
                    desc_label.text = "You should have already received your ticket via email. If not, please contact us via Instagram or email."
                else:
                    logger.error(str(e))
                    status_icon.set_name('close')
                    status_icon.classes(replace='text-red-500')
                    status_label.text = "Unable to process payment."
                    desc_label.text = "Please check your email. If you haven't received a ticket from us, contact us via Instagram or email."

                secondary_button("go home").on_click(
                    lambda: ui.navigate.to("/"))
                return f

            sp.set_visibility(False)
            status_icon.set_visibility(True)

            if confirm_response.status == PaymentStatus.CONFIRMED:
                status_label.text = "Payment succesful!"
                desc_label.text = "Each person will receive their ticket via email."
                secondary_button("Event Information").on_click(
                    lambda: ui.navigate.to(f"/event/{confirm_response.event_id}"))

            else:
                async def get_new_link(person_id, event_id):
                    new_link_btn.props(add='loading')
                    try:
                        person = await client.fetch_person(person_id)
                        await client.verify_person(VerifyPersonRequest(email=person.email, event_id=event_id))
                        ui.notify("Check your email!", type='positive')
                    except Exception as e:
                        ui.notify(
                            "Unable to send a payment link. Please use your existing link in your email or try again later.", type='negative')
                        logger.error(str(e))
                    finally:
                        new_link_btn.props(remove='loading')

                status_icon.set_name('close')
                status_icon.classes(replace='text-red-500')
                status_label.text = "Payment Failed"
                desc_label.text = confirm_response.description if confirm_response.description else ""
                new_link_btn = secondary_button('get new link').on_click(lambda: get_new_link(
                    confirm_response.person_id, confirm_response.event_id))
    return f


@ui.page('/ameriatransactionstate', title='Payment Confirmation | Drop Dead Disco')
async def myameria_callback(client: Client, transactionId: int, paymentId: UUID, status=myameria_payment_status, errorMessage: Optional[str] = None):
    await client.connected()
    client.content.classes('p-0')
    if not transactionId or not paymentId or not status:
        raise HTTPException(404)

    confirm_request = PaymentConfirmRequest(
        order_id=int(transactionId),
        provider=PaymentProvider.MYAMERIA,
        payment_id=paymentId
    )

    await callback_page(confirm_request)


@ui.page('/vpostransactionstate', title='Payment Confirmation | Drop Dead Disco')
async def vpos_callback(client: Client, orderID: int, resposneCode: str, paymentID: UUID, opaque: Optional[str] = None, description: Optional[str] = None):
    await client.connected()
    if not orderID or not resposneCode or not paymentID:
        raise HTTPException(404)

    confirm_request = PaymentConfirmRequest(
        order_id=int(orderID),
        provider=PaymentProvider.VPOS,
        payment_id=paymentID
    )

    await callback_page(confirm_request)
