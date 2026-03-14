import os
import jwt
from uuid import uuid4
from datetime import timezone, datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from decorators import with_db

TOKEN_EXPIRATION_MINUTES = 15
auth_secret = os.environ['auth_secret']


def safe_redirect_url(url: str) -> str:
    if url and url.startswith('/') and not url.startswith('//'):
        return url
    return '/'


async def create_email_token(email: str, expires_in: int = TOKEN_EXPIRATION_MINUTES) -> str:
    return jwt.encode({
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in),
        "iat": datetime.now(timezone.utc).timestamp(),
    }, auth_secret, algorithm="HS256")


async def create_session_token(person_id, expires_in: int = TOKEN_EXPIRATION_MINUTES, refresh: bool = False) -> str:
    data = {
        "person_id": person_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in),
        "iat": datetime.now(timezone.utc).timestamp(),
    }
    if refresh:
        data['jti'] = str(uuid4())
    return jwt.encode(data, auth_secret, algorithm="HS256")


async def create_signup_token(email: str, expires_in: int = 30, **extra) -> str:
    payload = {
        "type": "signup",
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in),
        "iat": datetime.now(timezone.utc).timestamp(),
        **extra,
    }
    return jwt.encode(payload, auth_secret, algorithm="HS256")


def decode_signup_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, auth_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Signup link expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid signup token")
    if payload.get("type") != "signup":
        raise HTTPException(400, "Invalid token type")
    return payload


@with_db
async def generate_and_set_tokens(db: AsyncSession, person_id: str, refresh_expiry: int = 7 * 24 * 60, redirect_url='/'):
    from db_models import RefreshToken

    access = await create_session_token(str(person_id))
    refresh = await create_session_token(str(person_id), expires_in=refresh_expiry, refresh=True)

    db.add(RefreshToken(token=refresh, person_id=person_id))
    await db.commit()

    response = RedirectResponse(safe_redirect_url(redirect_url), 302)
    response.set_cookie(
        "access_token", access,
        httponly=True, secure=True, samesite="lax",
        max_age=15 * 60, path="/"
    )
    response.set_cookie(
        "refresh_token", refresh,
        httponly=True, secure=True, samesite="lax",
        max_age=7 * 24 * 3600, path="/"
    )
    return response


@with_db
async def refresh_session(db: AsyncSession, request: Request):
    from db_models import RefreshToken, Person
    from enums import PersonStatus

    token = request.cookies.get('refresh_token')
    if not token:
        raise HTTPException(401, "No refresh token")

    try:
        payload = jwt.decode(token, auth_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid")

    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token == token))
    if not stored:
        raise HTTPException(401, "Token revoked")

    person = await db.get(Person, payload['person_id'])
    if not person or person.status == PersonStatus.rejected:
        raise HTTPException(403, "Rejected")

    await db.delete(stored)
    return await generate_and_set_tokens(payload['person_id'], redirect_url=str(request.url))


@with_db
async def logout_session(db: AsyncSession, token: str = None, redirect_url='/'):
    from db_models import RefreshToken

    response = RedirectResponse(redirect_url, 302)
    response.delete_cookie('access_token', secure=True, httponly=True, samesite="lax")
    response.delete_cookie('refresh_token', secure=True, httponly=True, samesite="lax")

    if token:
        stored = await db.scalar(select(RefreshToken).where(RefreshToken.token == token))
        if stored:
            await db.delete(stored)
            await db.commit()

    return response
