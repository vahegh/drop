"""
Top-level payment callback routes that payment providers redirect the browser to.
These routes do any required server-side work (e.g. card binding) then redirect
the user to the appropriate React page.
"""
import logging
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

from decorators import verify_user_token
from api_models import CardBindingCreate
from services.card_binding import create_card_binding
from services.vpos_payment import get_payment_details_vpos, get_card_binding_vpos

logger = logging.getLogger(__name__)

router = APIRouter(include_in_schema=False)


@router.get("/cardbinding")
async def card_binding_callback(
    request: Request,
    orderID: Optional[int] = None,
    paymentID: Optional[UUID] = None,
    opaque: Optional[str] = None,
    resposneCode: Optional[str] = None,
):
    """VPOS redirects here after a card-binding-only payment (add payment method flow)."""
    try:
        person = await verify_user_token(request)
    except HTTPException:
        return RedirectResponse("/profile")

    if opaque and paymentID:
        try:
            payment_details = await get_payment_details_vpos(paymentID)
            if payment_details.ResponseCode == "00":
                card_binding_vpos = await get_card_binding_vpos(opaque)
                if card_binding_vpos:
                    await create_card_binding(CardBindingCreate(
                        id=opaque,
                        person_id=person.id,
                        masked_card_number=card_binding_vpos.CardPan,
                        card_expiry_date=card_binding_vpos.ExpDate,
                        is_active=card_binding_vpos.IsAvtive
                    ))
        except Exception as e:
            logger.warning(f"Card binding callback error: {str(e)}")

    return RedirectResponse("/profile?card_added=1")
