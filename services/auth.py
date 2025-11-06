import os
import jwt
from uuid import uuid4
from datetime import timezone, datetime, timedelta
from fastapi import HTTPException, Request, Depends
from db import with_db
from sqlalchemy.ext.asyncio import AsyncSession
from db_models import Person
from enums import PersonStatus
from consts import admins

TOKEN_EXPIRATION_MINUTES = 15
auth_secret = os.environ['auth_secret']


async def create_jwt(email, event_id, expires_in: int = TOKEN_EXPIRATION_MINUTES):
    token = jwt.encode({
        "email": email,
        "event_id": event_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in),
        "iat": datetime.now(timezone.utc).timestamp()
    }, auth_secret, algorithm="HS256")

    return token


async def create_token(person_id, expires_in: int = TOKEN_EXPIRATION_MINUTES, refresh: bool = False):
    data = {
        "person_id": person_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in),
        "iat": datetime.now(timezone.utc).timestamp()
    }
    if refresh:
        jti = str(uuid4())
        data['jti'] = jti

    token = jwt.encode(data, auth_secret, algorithm="HS256")

    return token


@with_db
async def verify_user_token(db: AsyncSession, request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(401, "Not authenticated")

    try:
        payload = jwt.decode(token, auth_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid")

    person = await db.get(Person, payload['person_id'])
    if not person:
        raise HTTPException(404, "No such person")

    if person.status == PersonStatus.rejected:
        raise HTTPException(403, "Rejected")

    return person


async def verify_admin_token(request: Request):
    person = await verify_user_token(request)
    if person.email not in admins:
        raise HTTPException(403, "Admin only")
    return person
