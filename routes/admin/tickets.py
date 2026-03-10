from uuid import UUID
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from decorators import with_db
from sqlalchemy.ext.asyncio import AsyncSession
from db_models import EventTicket

router = APIRouter(tags=["Admin Tickets"], prefix="/tickets")


@router.delete("/{id}", status_code=204)
async def delete_ticket(id: UUID):
    return await _delete_ticket(id)


@with_db
async def _delete_ticket(db: AsyncSession, id: UUID):
    ticket = await db.get(EventTicket, id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    await db.delete(ticket)
    await db.commit()
    return Response(status_code=204)
