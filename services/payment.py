import os
from uuid import UUID
from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from decorators import with_db
from services.ecrm import ecrm_print
from services.member_pass import send_member_pass
from consts import APP_BASE_URL_NO_PROTO
from enums import PersonStatus, PaymentStatus, PaymentProvider
from services.telegram import notify_payment_confirmed
from services.myameria_payment import MYAMERIA_PAY_URL, myameria_merchant_id
from db_models import Payment, Person, EventTicket, PaymentIntent, TicketTier, Event, MemberPass, DrinkVoucher
from services.event_ticket import add_ticket_to_db, create_event_ticket, send_event_ticket
from services.myameria_payment import create_payment_myameria, get_payment_details_myameria, refund_payment_myameria
from services.vpos_payment import init_payment_vpos, get_payment_details_vpos, get_card_binding_vpos, VPOS_BASE_URL, cancel_payment_vpos
from services.card_binding import create_card_binding
from services.drink_payment_intent import get_drink_payment_intents, delete_drink_payment_intents
from services.drink_voucher import create_drink_voucher
from services.payment_intent import delete_payment_intent
from api_models import PaymentConfirmRequest, PaymentConfirmResponse, ECRMPrintRequest, ECRMItem, PaymentUpdate, MyAmeriaPaymentRefundRequest, CardBindingCreate
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
    logger.info(f"Initializing payment {payment.order_id}")
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

        case PaymentProvider.APPLEPAY | PaymentProvider.GOOGLEPAY:
            try:
                payment_id = await init_payment_vpos(payment.order_id, payment.amount, save_card=save_card)
                payment.upstream_payment_id = payment_id
                payment = await create_payment(payment)

                url = f"{VPOS_BASE_URL}/Payments/Pay?id={payment_id}&lang=en&type=13"
                return url

            except Exception as e:
                raise HTTPException(
                    500, f"Unable to create Apple Pay / Google Pay payment: {str(e)}")

        case PaymentProvider.MYAMERIA:
            try:
                await create_payment_myameria(payment.order_id, payment.amount)
                url = f"{MYAMERIA_PAY_URL}?merchantName=Drop+Dead+Disco&transactionAmount={str(payment.amount)}&transactionId={str(payment.order_id)}&merchantId={myameria_merchant_id}&terminalId={myameria_merchant_id}&callbackscheme={APP_BASE_URL_NO_PROTO}"
                return url
            except Exception as e:
                raise HTTPException(500, f"Unable to create MyAmeria payment: {str(e)}")

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

    logger.info(f"Attempting to confirm payment {payment.order_id}")

    ticket_holders = (await db.scalars(select(Person)
                                       .join(PaymentIntent, PaymentIntent.recipient_id == Person.id)
                                       .where(PaymentIntent.order_id == payment.order_id))).all()

    # Pre-fetch payment intents with tier snapshots before they get deleted below
    all_intents = (await db.scalars(select(PaymentIntent).where(PaymentIntent.order_id == payment.order_id))).all()

    match transaction.provider:
        case PaymentProvider.VPOS | PaymentProvider.APPLEPAY | PaymentProvider.GOOGLEPAY:
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

                if transaction.opaque and payment.status == PaymentStatus.CONFIRMED:
                    try:
                        card_binding_vpos = await get_card_binding_vpos(transaction.opaque)
                        if card_binding_vpos:
                            await create_card_binding(CardBindingCreate(
                                id=transaction.opaque,
                                person_id=payment.person_id,
                                masked_card_number=card_binding_vpos.CardPan,
                                card_expiry_date=card_binding_vpos.ExpDate,
                                is_active=card_binding_vpos.IsAvtive
                            ))
                    except Exception as e:
                        logger.warning(f"Unable to save card binding: {str(e)}")

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

        if ticket_holders:
            for h in ticket_holders:
                recipient_names.append(f"{h.first_name} {h.last_name}")
                if h.status == PersonStatus.pending:
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

                await delete_payment_intent(payment.order_id, h.id)

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
            adg_code = "79.90"

            # Group intents by tier snapshot
            tier_groups: dict[tuple, int] = {}

            for intent in all_intents:
                if intent.tier_id is not None and intent.tier_price is not None:
                    tier_obj = await db.get(TicketTier, intent.tier_id)
                    key = (
                        intent.tier_price,
                        tier_obj.ecrm_good_code if tier_obj else "0001",
                        tier_obj.ecrm_good_name if tier_obj else "General Admission Event Entry",
                    )
                    tier_groups[key] = tier_groups.get(key, 0) + 1

            for (price, code, name), qty in tier_groups.items():
                items.append(ECRMItem(quantity=qty, price=price, adgCode=adg_code, goodCode=code, goodName=name))

            print_req = ECRMPrintRequest(crn=ecrm_crn, cardAmount=payment.amount, items=items)

            await ecrm_print(print_req)

        await notify_payment_confirmed(person, payment, recipient_names)

    db.add(payment)
    await db.commit()
    return confirm_response


async def refund_payment(payment: Payment):
    match payment.provider:
        case PaymentProvider.VPOS | PaymentProvider.APPLEPAY | PaymentProvider.GOOGLEPAY:
            await cancel_payment_vpos(payment.upstream_payment_id)

        case PaymentProvider.MYAMERIA:
            await refund_payment_myameria(
                MyAmeriaPaymentRefundRequest(transactionId=str(payment.order_id))
            )

        case _:
            raise ValueError(f"Unsupported payment provider for refund: {payment.provider}")

    payment = await update_payment(
        payment.order_id,
        PaymentUpdate(
            status=PaymentStatus.REFUNDED
        )
    )

    logger.info(f"Order {payment.order_id} refunded")
    return payment
