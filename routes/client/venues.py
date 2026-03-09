from uuid import UUID
from fastapi import APIRouter
from services.venue import get_venue_info

router = APIRouter(tags=["Client Venues"], prefix="/venues")


@router.get("/{id}")
async def venue_detail(id: UUID):
    return await get_venue_info(id)
