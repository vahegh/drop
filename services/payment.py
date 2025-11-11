import os
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from decorators import with_db
from consts import APP_BASE_URL_NO_PROTO, idram_merchant_id
from enums import PersonStatus, PaymentStatus, PaymentProvider
from db_models import Payment, Person, EventTicket, PaymentIntent, Event, MemberPass
from services.ecrm import ecrm_print
from services.telegram import notify_payment_init, notify_payment_confirmed
from services.event_ticket import add_ticket_to_db, create_event_ticket, send_event_ticket
from services.myameria_payment import MYAMERIA_PAY_URL, myameria_merchant_id
from services.myameria_payment import create_payment_myameria, get_payment_details_myameria
from services.vpos_payment import init_payment_vpos, get_payment_details_vpos, VPOS_BASE_URL
from services.member_pass import send_member_pass
from api_models import PaymentCreate, PaymentConfirmRequest, PaymentConfirmResponse, ECRMPrintRequest, ECRMItem

ecrm_crn = os.environ['ecrm_crn']


@with_db
async def get_all_payments(db: AsyncSession):
    payments = await db.scalars(select(Payment))
    return payments.all()


@with_db
async def init_payment(db: AsyncSession, request: PaymentCreate):
    new_payment = Payment(
        person_id=request.person_id,
        event_id=request.event_id,
        amount=request.amount,
        provider=request.provider
    )

    db.add(new_payment)
    await db.flush()

    recipient_names = []

    for id in request.ticket_holders:
        recipient = await db.get(Person, id)
        recipient_names.append(f"{recipient.first_name} {recipient.last_name}")
        intent = PaymentIntent(
            order_id=new_payment.order_id,
            recipient_id=id)
        db.add(intent)

    await db.commit()

    person = await db.get(Person, request.person_id)
    await notify_payment_init(person, new_payment, recipient_names)

    match request.provider:
        case PaymentProvider.VPOS:
            try:
                payment_id = await init_payment_vpos(new_payment.order_id, new_payment.amount)
                new_payment.upstream_payment_id = payment_id
                db.add(new_payment)
                await db.commit()

                url = f"{VPOS_BASE_URL}/Payments/Pay?id={payment_id}&lang=en"
                return url
            except Exception as e:
                raise HTTPException(500, f"Unable to create vPOS payment: {str(e)}")

        case PaymentProvider.MYAMERIA:
            try:
                await create_payment_myameria(new_payment.order_id, new_payment.amount)
                url = f"{MYAMERIA_PAY_URL}?merchantName=Drop+Dead+Disco&transactionAmount={str(new_payment.amount)}&transactionId={str(new_payment.order_id)}&merchantId={myameria_merchant_id}&terminalId={myameria_merchant_id}&callbackscheme={APP_BASE_URL_NO_PROTO}"
                return url
            except Exception as e:
                raise HTTPException(500, f"Unable to create MyAmeria payment: {str(e)}")

        case PaymentProvider.IDRAM:
            url = f"idramapp://payment?receiverName=Drop+Dead+Disco&receiverId={idram_merchant_id}&title={str(new_payment.order_id)}&amount={str(new_payment.amount)}"
            return url

        case _:
            raise HTTPException(404, "Payment provider not found")


@with_db
async def confirm_payment(db: AsyncSession, transaction: PaymentConfirmRequest):
    payment = await db.scalar(select(Payment).where((Payment.order_id == transaction.order_id) & (Payment.provider == transaction.provider)))
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
        case PaymentProvider.VPOS:
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

        member_qty = 0
        non_member_qty = 0

        recipient_names = []

        for h in ticket_holders:
            recipient_names.append(h.name)
            if h.status == PersonStatus.member:
                member_qty += 1
            else:
                non_member_qty += 1
        person = await db.get(Person, payment.person_id)
        await notify_payment_confirmed(person, payment, recipient_names)

        items = []

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

        ecrm_response = await ecrm_print(print_req)
        print(ecrm_response)

        for holder in ticket_holders:
            event_ticket = EventTicket(
                person_id=holder.id, event_id=payment.event_id, payment_order_id=payment.order_id)
            if holder.status == PersonStatus.member:
                await add_ticket_to_db(event_ticket)
                member_pass = await db.scalar(select(MemberPass).where(MemberPass.person_id == holder.id))
                await send_member_pass(member_pass, purchase=True)

            else:
                await create_event_ticket(event_ticket)
                await send_event_ticket(event_ticket)

    db.add(payment)
    await db.commit()
    return confirm_response
