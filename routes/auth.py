import os
import jwt
from sqlalchemy import select
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from decorators import with_db
from consts import APPLICATION_SUBMITTED_SUBJECT, APPLICATION_SUBMITTED_TEMPLATE
from api_models import PersonCreate, PersonUpdate
from services.person import update_person, create_person
from services.auth import create_jwt, create_token
from services.telegram import notify_application
from services.templating import generate_template
from services.mailing import EmailRequest, send_email
from enums import PersonStatus
from db_models import Person, RefreshToken
import logging

logger = logging.getLogger(__name__)


aud = os.environ['google_client_id']
client_secret = os.environ['google_client_secret']
auth_secret = os.environ['auth_secret']

router = APIRouter(tags=['Auth'], prefix="/api/auth")


def safe_redirect_url(url: str) -> str:
    if url and url.startswith('/') and not url.startswith('//'):
        return url
    return '/'


@with_db
async def generate_and_set_tokens(db: AsyncSession, person_id: str, refresh_expiry: int = 7*24*60, redirect_url='/'):
    access = await create_token(str(person_id))
    refresh = await create_token(str(person_id), expires_in=refresh_expiry, refresh=True)

    db.add(RefreshToken(token=refresh, person_id=person_id))
    await db.commit()

    response = RedirectResponse(safe_redirect_url(redirect_url), 302)

    response.set_cookie(
        "access_token", access,
        httponly=True, secure=True, samesite="lax",
        max_age=15*60, path="/"
    )

    response.set_cookie(
        "refresh_token", refresh,
        httponly=True, secure=True, samesite="lax",
        max_age=7*24*3600, path="/"
    )

    return response


@router.get("/login-user")
@with_db
async def login_user(db: AsyncSession, token, redirect_url='/'):
    try:
        id_info = id_token.verify_oauth2_token(
            token, requests.Request(), aud, clock_skew_in_seconds=5)

    except ValueError:
        raise HTTPException(401, "Invalid ID token")

    else:
        email = id_info['email']
        person = await db.scalar(select(Person).where(Person.email == email))
        if not person:
            return RedirectResponse(f"/signup?token={token}&redirect_url={redirect_url}", 302)

        if person.status == PersonStatus.rejected:
            raise HTTPException(401, "Rejected")

        avatar_url = id_info.get('picture')

        if avatar_url and not person.avatar_url:
            update_req = PersonUpdate(avatar_url=avatar_url)
            await update_person(person.id, update_req)

        logger.info(f"{person.email} login successful")

        return await generate_and_set_tokens(person.id, redirect_url=redirect_url)


@with_db
async def refresh(db: AsyncSession, request: Request):
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
async def logout(db: AsyncSession, token: str = None, redirect_url='/'):
    response = RedirectResponse(redirect_url, 302)

    if not token:
        return response

    response.delete_cookie(
        'access_token',
        secure=True,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        'refresh_token',
        secure=True,
        httponly=True,
        samesite="lax",
    )

    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token == token))

    if not stored:
        return response

    await db.delete(stored)
    await db.commit()

    return response
