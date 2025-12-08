from fastapi import APIRouter
from services.event import create_event
from api_models import EventCreate

router = APIRouter(tags=['Event'], prefix="/api/event")


@router.post("/")
async def create_event_api(event: EventCreate):
    return await create_event(event)
