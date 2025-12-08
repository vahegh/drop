from fastapi import APIRouter
from services.event import event_announcement

router = APIRouter(tags=['Event'], prefix="/api/event")


# @router.post("/announce")
# async def create_event_api(event_id):
#     return await event_announcement(event_id)
