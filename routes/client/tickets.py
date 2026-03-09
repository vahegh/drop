from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Request
from decorators import verify_user_token
from services.event_ticket import get_tickets_by_person_id

router = APIRouter(tags=["Client Tickets"], prefix="/tickets")


@router.get("")
async def list_tickets(request: Request, event_id: Optional[UUID] = None):
    person = await verify_user_token(request)
    return await get_tickets_by_person_id(person.id, event_id)
