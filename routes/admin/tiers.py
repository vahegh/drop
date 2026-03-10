from uuid import UUID
from fastapi import APIRouter
from api_models import TicketTierCreate, TicketTierUpdate, TicketTierResponse
from services.ticket_tier import get_tiers_for_event, get_tier, create_tier, update_tier, delete_tier

router = APIRouter(tags=["Admin Tiers"], prefix="/events/{event_id}/tiers")


@router.get("", response_model=list[TicketTierResponse])
async def list_tiers(event_id: UUID):
    return await get_tiers_for_event(event_id)


@router.post("", response_model=TicketTierResponse, status_code=201)
async def add_tier(event_id: UUID, body: TicketTierCreate):
    return await create_tier(event_id, body)


@router.patch("/{tier_id}", response_model=TicketTierResponse)
async def edit_tier(event_id: UUID, tier_id: UUID, body: TicketTierUpdate):
    return await update_tier(tier_id, body)


@router.delete("/{tier_id}", status_code=204)
async def remove_tier(event_id: UUID, tier_id: UUID):
    await delete_tier(tier_id)
