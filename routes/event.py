from fastapi import APIRouter
from services.event import event_announcement
from services.member_pass import update_apple_member_pass

router = APIRouter(tags=['Event'], prefix="/api/event")


# @router.post("/announce")
# async def create_event_api(event_id):
#     return await event_announcement(event_id)


# @router.get("/update-member-pass")
# async def update_member_pass():
#     return await update_apple_member_pass()
