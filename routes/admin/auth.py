import os
from sqlalchemy import select
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from decorators import with_db, verify_admin_token
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from db_models import Person
from services.auth import create_session_token
from consts import admins, google_client_id

router = APIRouter(tags=["Admin Auth"], prefix="/auth")


class GoogleLoginRequest(BaseModel):
    id_token: str


@router.post("/google")
@with_db
async def admin_google_login(db: AsyncSession, body: GoogleLoginRequest):
    try:
        id_info = id_token.verify_oauth2_token(
            body.id_token, google_requests.Request(), google_client_id,
            clock_skew_in_seconds=5,
        )
    except ValueError:
        raise HTTPException(401, "Invalid Google token")

    email = id_info.get("email")
    if not email or email not in admins:
        raise HTTPException(403, "Not an admin")

    person = await db.scalar(select(Person).where(Person.email == email))
    if not person:
        raise HTTPException(404, "Person not found")

    access_token = await create_session_token(str(person.id), expires_in=60 * 24 * 7)
    return {"access_token": access_token}


@router.get("/me")
async def admin_me(person: Person = Depends(verify_admin_token)):
    return {
        "id": str(person.id),
        "email": person.email,
        "first_name": person.first_name,
        "last_name": person.last_name,
    }
