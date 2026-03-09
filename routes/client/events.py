from uuid import UUID
from fastapi import APIRouter, HTTPException
from services.event import get_all_events, get_next_event, get_event_info

router = APIRouter(tags=["Client Events"], prefix="/events")


@router.get("")
async def list_events():
    return await get_all_events()


@router.get("/next")
async def next_event():
    event = await get_next_event()
    if not event:
        return None
    return event


@router.get("/{id}")
async def event_detail(id: UUID):
    event = await get_event_info(id)
    if not event:
        raise HTTPException(404, "Event not found")
    return event
