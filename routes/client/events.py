import re
from uuid import UUID
from typing import List
import httpx
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


@router.get("/{id}/photos", response_model=List[str])
async def event_photos(id: UUID):
    event = await get_event_info(id)
    if not event:
        raise HTTPException(404, "Event not found")
    if not event.album_url:
        return []
    async with httpx.AsyncClient() as client:
        response = await client.get(event.album_url, follow_redirects=True)
        urls = re.findall(r'https://lh3\.googleusercontent\.com/pw/[A-Za-z0-9_-]+', response.text)
        return list(set(urls))
