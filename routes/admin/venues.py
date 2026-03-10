from uuid import UUID
from fastapi import APIRouter
from fastapi.responses import Response
from api_models import VenueCreate, VenueUpdate
from services.venue import get_all_venues, get_venue_info, create_venue, update_venue, delete_venue

router = APIRouter(tags=["Admin Venues"], prefix="/venues")


@router.get("")
async def list_venues():
    return await get_all_venues()


@router.get("/{id}")
async def venue_detail(id: UUID):
    return await get_venue_info(id)


@router.post("", status_code=201)
async def create_venue_endpoint(body: VenueCreate):
    return await create_venue(body)


@router.patch("/{id}")
async def update_venue_endpoint(id: UUID, body: VenueUpdate):
    return await update_venue(id, body)


@router.delete("/{id}", status_code=204)
async def delete_venue_endpoint(id: UUID):
    await delete_venue(id)
    return Response(status_code=204)
