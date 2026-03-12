import re
import time
from uuid import UUID
from typing import List, Optional
import httpx
from fastapi import APIRouter, HTTPException
from services.event import get_all_events, get_next_event, get_event_info
from consts import all_photos_url

router = APIRouter(tags=["Client Events"], prefix="/events")

_PHOTO_CACHE_TTL = 50 * 60  # 50 minutes, matches frontend staleTime
_all_photos_cache: Optional[tuple[float, List[str]]] = None
_event_photos_cache: dict[UUID, tuple[float, List[str]]] = {}


async def _fetch_photos(url: str) -> List[str]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True)
        urls = re.findall(r'https://lh3\.googleusercontent\.com/pw/[A-Za-z0-9_-]+', response.text)
        return list(set(urls))


@router.get("")
async def list_events():
    return await get_all_events()


@router.get("/next")
async def next_event():
    event = await get_next_event()
    if not event:
        return None
    return event


@router.get("/photos", response_model=List[str])
async def all_photos():
    global _all_photos_cache
    now = time.monotonic()
    if _all_photos_cache and (now - _all_photos_cache[0]) < _PHOTO_CACHE_TTL:
        return _all_photos_cache[1]
    urls = await _fetch_photos(all_photos_url)
    _all_photos_cache = (now, urls)
    return urls


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
    now = time.monotonic()
    cached = _event_photos_cache.get(id)
    if cached and (now - cached[0]) < _PHOTO_CACHE_TTL:
        return cached[1]
    urls = await _fetch_photos(event.album_url)
    _event_photos_cache[id] = (now, urls)
    return urls
