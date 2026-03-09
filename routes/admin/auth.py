import os
from sqlalchemy import select
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from decorators import with_db
from sqlalchemy.ext.asyncio import AsyncSession
from db_models import Person
from services.auth import create_token
from consts import admins

router = APIRouter(tags=["Admin Auth"], prefix="/auth")

admin_password = os.environ.get("admin_password", "")


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
@with_db
async def admin_login(db: AsyncSession, body: AdminLoginRequest):
    if body.email not in admins:
        raise HTTPException(403, "Not an admin")
    if not admin_password or body.password != admin_password:
        raise HTTPException(401, "Invalid credentials")

    person = await db.scalar(select(Person).where(Person.email == body.email))
    if not person:
        raise HTTPException(404, "Person not found")

    access_token = await create_token(str(person.id), expires_in=60 * 24 * 7)
    return {"access_token": access_token}
