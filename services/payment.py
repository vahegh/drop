import os
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from decorators import with_db
from services.ecrm import ecrm_print
from services.member_pass import send_member_pass
from consts import APP_BASE_URL_NO_PROTO, idram_merchant_id
from enums import PersonStatus, PaymentStatus, PaymentProvider
from services.telegram import notify_payment_confirmed
from services.myameria_payment import MYAMERIA_PAY_URL, myameria_merchant_id
from db_models import Payment, Person, EventTicket, PaymentIntent, Event, MemberPass, DrinkVoucher
from services.event_ticket import add_ticket_to_db, create_event_ticket, send_event_ticket
from services.myameria_payment import create_payment_myameria, get_payment_details_myameria, refund_payment_myameria
from services.vpos_payment import init_payment_vpos, get_payment_details_vpos, VPOS_BASE_URL, cancel_payment_vpos
from services.drink_payment_intent import get_drink_payment_intents, delete_drink_payment_intents
from services.drink_voucher import create_drink_voucher
from services.payment_intent import delete_payment_intents
from api_models import PaymentConfirmRequest, PaymentConfirmResponse, ECRMPrintRequest, ECRMItem, PaymentUpdate, MyAmeriaPaymentRefundRequest
import logging

ecrm_crn = os.environ['ecrm_crn']
logger = logging.getLogger(__name__)


@with_db
async def get_all_payments(db: AsyncSession):
    payments = await db.scalars(select(Payment))
    return payments.all()


@with_db
async def get_payment(db: AsyncSession, order_id: int):
    return await db.get(Payment, order_id)


@with_db
async def get_ticket_payment(db: AsyncSession, person_id: UUID, event_id: UUID):
    payment = await db.scalar(select(Payment).where(Payment.person_id == person_id).where(Payment.event_id == event_id))
    return payment


@with_db
async def create_payment(db: AsyncSession, payment: Payment):
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@with_db
async def update_payment(db: AsyncSession, order_id: int, updated_payment: PaymentUpdate):
    payment = await get_payment(order_id)
    if not payment:
        raise ValueError(f"No payment with order_id {order_id}")

    for field, value in updated_payment.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)

    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def init_payment(payment: Payment, save_card=False):
    match payment.provider:
        case PaymentProvider.VPOS:
            try:
                payment_id = await init_payment_vpos(payment.order_id, payment.amount, save_card=save_card)
                payment.upstream_payment_id = payment_id
                payment = await create_payment(payment)

                url = f"{VPOS_BASE_URL}/Payments/Pay?id={payment_id}&lang=en&type=5"
                return url

            except Exception as e:
                raise HTTPException(500, f"Unable to create vPOS payment: {str(e)}")

        case PaymentProvider.APPLEPAY:
            try:
                payment_id = await init_payment_vpos(payment.order_id, payment.amount, save_card=save_card)
                payment.upstream_payment_id = payment_id
                payment = await create_payment(payment)

                url = f"{VPOS_BASE_URL}/Payments/Pay?id={payment_id}&lang=en&type=13"
                return url

            except Exception as e:
                raise HTTPException(500, f"Unable to create Apple Pay payment: {str(e)}")

        case PaymentProvider.MYAMERIA:
            try:
                await create_payment_myameria(payment.order_id, payment.amount)
                url = f"{MYAMERIA_PAY_URL}?merchantName=Drop+Dead+Disco&transactionAmount={str(payment.amount)}&transactionId={str(payment.order_id)}&merchantId={myameria_merchant_id}&terminalId={myameria_merchant_id}&callbackscheme={APP_BASE_URL_NO_PROTO}"
                return url
            except Exception as e:
                raise HTTPException(500, f"Unable to create MyAmeria payment: {str(e)}")

        case PaymentProvider.IDRAM:
            url = f"idramapp://payment?receiverName=Drop+Dead+Disco&receiverId={idram_merchant_id}&title={str(payment.order_id)}&amount={str(payment.amount)}"
            return url

        case _:
            raise HTTPException(404, "Payment provider not found")


@with_db
async def confirm_payment(db: AsyncSession, transaction: PaymentConfirmRequest, print_receipt=True):
    payment = await get_payment(transaction.order_id)
    if not payment:
        raise HTTPException(404, "Payment not found")

    if payment.status == PaymentStatus.CONFIRMED:
        raise HTTPException(409, f"This payment is already processed")

    if payment.status is not PaymentStatus.CREATED:
        raise HTTPException(400, f"Invalid payment status: {payment.status.value}")

    ticket_holders = (await db.scalars(select(Person)
                                       .join(PaymentIntent, PaymentIntent.recipient_id == Person.id)
                                       .where(PaymentIntent.order_id == payment.order_id))).all()

    match transaction.provider:
        case PaymentProvider.VPOS | PaymentProvider.APPLEPAY:
            try:
                payment_details = await get_payment_details_vpos(payment.upstream_payment_id)
                if payment_details.ResponseCode == "00":
                    payment.status = PaymentStatus.CONFIRMED

                confirm_response = PaymentConfirmResponse(
                    order_id=payment_details.OrderID,
                    provider=transaction.provider,
                    payment_id=transaction.payment_id,
                    status=payment.status,
                    description=payment_details.Description,
                    person_id=payment.person_id,
                    event_id=payment.event_id,
                    amount=payment.amount,
                    num_tickets=len(ticket_holders)
                )
            except Exception as e:
                raise HTTPException(500, f"Unable to check vPOS payment status: {str(e)}")

        case PaymentProvider.BINDING:
            if not transaction.payment_id:
                confirm_response = PaymentConfirmResponse(
                    order_id=payment.order_id,
                    provider=transaction.provider,
                    status=payment.status,
                    person_id=payment.person_id,
                    event_id=payment.event_id,
                    amount=payment.amount,
                    num_tickets=len(ticket_holders)
                )
            else:
                try:
                    payment.upstream_payment_id = transaction.payment_id

                    payment_details = await get_payment_details_vpos(transaction.payment_id)
                    if payment_details.ResponseCode == "00":
                        payment.status = PaymentStatus.CONFIRMED

                    confirm_response = PaymentConfirmResponse(
                        order_id=payment_details.OrderID,
                        provider=transaction.provider,
                        payment_id=transaction.payment_id,
                        status=payment.status,
                        description=payment_details.Description,
                        person_id=payment.person_id,
                        event_id=payment.event_id,
                        amount=payment.amount,
                        num_tickets=len(ticket_holders)
                    )

                except Exception as e:
                    raise HTTPException(500, f"Unable to check binding payment status: {str(e)}")

        case PaymentProvider.MYAMERIA:
            try:
                payment_details = await get_payment_details_myameria(transaction_id=str(transaction.order_id), payment_id=transaction.payment_id)
                payment.upstream_payment_id = transaction.payment_id

                if payment_details.isSuccessful:
                    payment.status = PaymentStatus.CONFIRMED

                confirm_response = PaymentConfirmResponse(
                    order_id=payment_details.transactionId,
                    provider=transaction.provider,
                    payment_id=payment_details.paymentId,
                    status=payment.status,
                    person_id=payment.person_id,
                    event_id=payment.event_id,
                    amount=payment.amount,
                    num_tickets=len(ticket_holders)
                )

            except Exception as e:
                raise HTTPException(500, f"Unable to check MyAmeria payment status: {str(e)}")

    if payment.status == PaymentStatus.CONFIRMED:
        person = await db.get(Person, payment.person_id)

        recipient_names = []
        items = []
        member_qty = 0
        non_member_qty = 0

        if ticket_holders:
            for h in ticket_holders:
                recipient_names.append(f"{h.first_name} {h.last_name}")
                if h.status == PersonStatus.member:
                    member_qty += 1
                elif h.status == PersonStatus.verified:
                    non_member_qty += 1
                elif h.status == PersonStatus.pending:
                    non_member_qty += 1
                    continue

                event_ticket = EventTicket(
                    person_id=h.id, event_id=payment.event_id, payment_order_id=payment.order_id)

                if h.status == PersonStatus.member:
                    await add_ticket_to_db(event_ticket)
                    member_pass = await db.scalar(select(MemberPass).where(MemberPass.person_id == h.id))
                    await send_member_pass(member_pass, purchase=True)

                else:
                    await create_event_ticket(event_ticket)
                    await send_event_ticket(event_ticket)

            if recipient_names:
                await delete_payment_intents(payment.order_id)

        drinks = await get_drink_payment_intents(payment.order_id)
        if drinks:
            for d in drinks:
                await create_drink_voucher(
                    DrinkVoucher(
                        person_id=person.id,
                        drink_id=d.drink_id,
                        payment_order_id=payment.order_id
                    )
                )
            await delete_drink_payment_intents(payment.order_id)

        if print_receipt:
            event = await db.get(Event, payment.event_id)
            if event.early_bird_date < datetime.now(timezone.utc):
                non_member_price = event.general_admission_price
                non_member_item_code = "0001"
                non_member_item_name = "General Admission Event Entry"
            else:
                non_member_price = event.early_bird_price
                non_member_item_code = "0002"
                non_member_item_name = "Early Bird Event Entry"

            member_item_code = "0003"
            member_item_name = "Member Event Entry"
            adg_code = "79.90"

            if member_qty:
                items.append(
                    ECRMItem(
                        quantity=member_qty,
                        price=event.member_ticket_price,
                        adgCode=adg_code,
                        goodCode=member_item_code,
                        goodName=member_item_name,
                    )
                )

            if non_member_qty:
                items.append(
                    ECRMItem(
                        quantity=non_member_qty,
                        price=non_member_price,
                        adgCode=adg_code,
                        goodCode=non_member_item_code,
                        goodName=non_member_item_name,
                    )
                )

            print_req = ECRMPrintRequest(crn=ecrm_crn, cardAmount=payment.amount, items=items)

            await ecrm_print(print_req)

        await notify_payment_confirmed(person, payment, recipient_names)

    db.add(payment)
    await db.commit()
    return confirm_response


async def refund_payment(payment: Payment):
    match payment.provider:
        case PaymentProvider.VPOS | PaymentProvider.APPLEPAY:
            try:
                await cancel_payment_vpos(payment.upstream_payment_id)
            except Exception as e:
                logger.error(f"Unable to cancel VPOS/ApplePay payment: {str(e)}")

        case PaymentProvider.MYAMERIA:
            try:
                await refund_payment_myameria(
                    MyAmeriaPaymentRefundRequest(transactionId=str(payment.order_id))
                )
            except Exception as e:
                logger.error(f"Unable to refund MyAmeria payment: {str(e)}")

        case PaymentProvider.IDRAM:
            logger.error("Idram selected for refund")

        case _:
            logger.error(f"Wrong payment provider: {payment.provider}")

    payment = await update_payment(
        payment.order_id,
        PaymentUpdate(
            status=PaymentStatus.REFUNDED
        )
    )
    return payment
