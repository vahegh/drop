from uuid import UUID
from fastapi import APIRouter
from fastapi.responses import Response
from api_models import EventCreate, EventUpdate
from services.event import get_all_events, get_event_info, create_event, update_event, delete_event

router = APIRouter(tags=["Admin Events"], prefix="/events")


@router.get("")
async def list_events():
    return await get_all_events()


@router.get("/{id}")
async def event_detail(id: UUID):
    return await get_event_info(id)


@router.post("", status_code=201)
async def create_event_endpoint(body: EventCreate):
    return await create_event(body)


@router.patch("/{id}")
async def update_event_endpoint(id: UUID, body: EventUpdate):
    return await update_event(id, body)


@router.delete("/{id}", status_code=204)
async def delete_event_endpoint(id: UUID):
    await delete_event(id)
    return Response(status_code=204)
