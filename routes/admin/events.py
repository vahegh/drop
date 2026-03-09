from uuid import UUID
from fastapi import APIRouter, Request
from decorators import verify_admin_token
from api_models import EventCreate, EventUpdate
from services.event import get_all_events, get_event_info, create_event, update_event

router = APIRouter(tags=["Admin Events"], prefix="/events")


@router.get("")
async def list_events(request: Request):
    await verify_admin_token(request)
    return await get_all_events()


@router.get("/{id}")
async def event_detail(id: UUID, request: Request):
    await verify_admin_token(request)
    return await get_event_info(id)


@router.post("", status_code=201)
async def create_event_endpoint(body: EventCreate, request: Request):
    await verify_admin_token(request)
    return await create_event(body)


@router.patch("/{id}")
async def update_event_endpoint(id: UUID, body: EventUpdate, request: Request):
    await verify_admin_token(request)
    return await update_event(id, body)
