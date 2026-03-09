from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from decorators import verify_admin_token, with_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db_models import Person
from enums import PersonStatus
from api_models import PersonUpdate
from services.person import update_person

router = APIRouter(tags=["Admin People"], prefix="/people")


class StatusUpdate(BaseModel):
    status: PersonStatus


@router.get("")
async def list_people(request: Request, status: Optional[str] = None):
    await verify_admin_token(request)
    return await _get_people(status)


@with_db
async def _get_people(db: AsyncSession, status: Optional[str]):
    q = select(Person)
    if status:
        q = q.where(Person.status == PersonStatus(status))
    q = q.order_by(Person.status, Person.first_name)
    result = await db.scalars(q)
    return result.all()


@router.patch("/{id}/status")
async def update_person_status(id: UUID, body: StatusUpdate, request: Request):
    await verify_admin_token(request)
    return await update_person(id, PersonUpdate(status=body.status))
