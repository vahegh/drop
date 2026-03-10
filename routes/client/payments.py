from datetime import timezone
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from decorators import verify_user_token
from enums import PaymentProvider, PersonStatus
from api_models import PaymentConfirmRequest, CardBindingUpdate
from consts import APP_BASE_URL
from db_models import Payment, PaymentIntent, DrinkPaymentIntent
from services.payment import create_payment, init_payment, confirm_payment
from services.payment_intent import create_payment_intent
from services.drink_payment_intent import create_drink_payment_intent
from services.person import get_person
from services.event import get_event_info
from services.ticket_tier import get_tiers_for_event, resolve_tier_for_person
from services.card_binding import get_card_binding_by_person_id, update_card_binding
from services.vpos_payment import make_binding_payment_vpos, deactivate_binding_vpos, init_payment_vpos, VPOS_BASE_URL
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Client Payments"], prefix="/payments")


class AttendeeItem(BaseModel):
    person_id: UUID


class InitiatePaymentRequest(BaseModel):
    event_id: UUID
    provider: PaymentProvider
    attendees: list[AttendeeItem]
    drink_ids: list[UUID] = []
    save_card: bool = False


class BindingPaymentRequest(BaseModel):
    order_id: int
    card_id: UUID
    amount: float


@router.post("")
async def initiate_payment(body: InitiatePaymentRequest, request: Request):
    # Auth is optional – guest checkout allowed; person_id defaults to first attendee
    person = None
    try:
        person = await verify_user_token(request)
    except HTTPException:
        pass

    event = await get_event_info(body.event_id)
    if not event:
        raise HTTPException(404, "Event not found")

    # Resolve tiers for this event
    tiers = await get_tiers_for_event(body.event_id)

    # Calculate total amount, resolving tier per attendee
    total = 0.0
    resolved_attendees = []  # list of (person, tier)
    for item in body.attendees:
        p = await get_person(item.person_id)
        if tiers:
            tier = resolve_tier_for_person(tiers, p.status)
            if not tier:
                raise HTTPException(422, f"No applicable ticket tier for attendee {p.id}")
        else:
            # Fallback: no tiers defined yet (stale state), use flat event pricing
            tier = None
            from datetime import datetime as _dt
            if p.status == PersonStatus.member:
                total += event.member_ticket_price
            elif event.early_bird_date and _dt.now(timezone.utc) < event.early_bird_date and event.early_bird_price:
                total += event.early_bird_price
            else:
                total += event.general_admission_price
        if tier:
            total += tier.price
        resolved_attendees.append((p, tier))

    # Add drinks
    if body.drink_ids:
        from services.drink import get_drink
        for drink_id in body.drink_ids:
            drink = await get_drink(drink_id)
            if drink:
                total += drink.price

    payer_id = person.id if person else resolved_attendees[0][0].id

    # Persist payment first to get autoincrement order_id
    new_payment = await create_payment(Payment(
        person_id=payer_id,
        event_id=body.event_id,
        amount=total,
        provider=body.provider,
    ))

    for attendee, tier in resolved_attendees:
        await create_payment_intent(
            PaymentIntent(
                order_id=new_payment.order_id,
                recipient_id=attendee.id,
                tier_id=tier.id if tier else None,
                tier_price=tier.price if tier else None,
            )
        )

    for drink_id in body.drink_ids:
        await create_drink_payment_intent(
            DrinkPaymentIntent(order_id=new_payment.order_id, drink_id=drink_id)
        )

    redirect_url = await init_payment(new_payment, save_card=body.save_card)
    return {"order_id": new_payment.order_id, "redirect_url": redirect_url}


@router.post("/binding")
async def binding_payment(body: BindingPaymentRequest, request: Request):
    person = await verify_user_token(request)
    resp = await make_binding_payment_vpos(body.card_id, body.order_id, body.amount)
    return {"order_id": body.order_id, "payment_id": resp.PaymentID}


@router.post("/confirm")
async def confirm(body: PaymentConfirmRequest):
    return await confirm_payment(body)


@router.get("/methods")
async def list_payment_methods(request: Request):
    person = await verify_user_token(request)
    return await get_card_binding_by_person_id(person.id)


@router.post("/methods")
async def add_payment_method(request: Request):
    person = await verify_user_token(request)
    # Create a small binding payment (10 AMD) to trigger card save
    new_payment = Payment(
        person_id=person.id,
        event_id=None,
        amount=10,
        provider=PaymentProvider.VPOS,
    )
    saved = await create_payment(new_payment)
    payment_id = await init_payment_vpos(
        saved.order_id, saved.amount, save_card=True,
        back_url=f"{APP_BASE_URL}/cardbinding"
    )
    redirect_url = f"{VPOS_BASE_URL}/Payments/Pay?id={payment_id}&lang=en&type=5"
    return {"redirect_url": redirect_url}




@router.delete("/methods/{id}")
async def remove_payment_method(id: UUID, request: Request):
    await verify_user_token(request)
    await deactivate_binding_vpos(id)
    await update_card_binding(id, CardBindingUpdate(is_active=False))
    return {"ok": True}
