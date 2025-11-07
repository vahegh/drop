import os
import jwt
from sqlalchemy import select
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from db import with_db
from consts import APP_BASE_URL, APPLICATION_SUBMITTED_SUBJECT, APPLICATION_SUBMITTED_TEMPLATE
from api_models import VerifyPersonRequest, ValidateTokenRequest, ValidateTokenResponse, PersonCreate, PersonUpdate
from routes.person import get_person_by_email, update_person
from routes.event import get_event_info
from routes.event_ticket import get_tickets_by_person_id
from services.event_ticket import create_event_ticket
from services.auth import create_jwt, create_token
from services.telegram import notify_application
from services.templating import generate_template
from services.mailing import EmailRequest, send_email
from enums import PersonStatus
from services.send_pass import send_magic_link, send_event_ticket
from db_models import Event, EventTicket, Person, RefreshToken
import logging

logger = logging.getLogger(__name__)


aud = os.environ['google_client_id']
auth_secret = os.environ['auth_secret']

router = APIRouter(tags=['Auth'], prefix="/api/auth")


@router.post("/verify-person")
@with_db
async def verify_person(db: AsyncSession, request: VerifyPersonRequest):
    try:
        person = await get_person_by_email(request.email)
    except HTTPException:
        raise

    event = await db.get(Event, request.event_id)
    if not event:
        raise HTTPException(404, "No such event")

    if person.status in (PersonStatus.verified, PersonStatus.member):
        token = await create_jwt(person.email, str(event.id))
        await send_magic_link(person, event.name, f"{APP_BASE_URL}/buy-ticket?token={token}")
    return


@router.post("/validate-token")
async def validate_token(request: ValidateTokenRequest):
    try:
        payload = jwt.decode(request.token, auth_secret, algorithms=["HS256"])
        try:
            person = await get_person_by_email(payload['email'])
            event = await get_event_info(payload['event_id'])
            has_ticket = bool(await get_tickets_by_person_id(person.id, event.id))
        except HTTPException(404):
            raise
        else:
            return ValidateTokenResponse(person=person, event=event, has_ticket=has_ticket)

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid")


@router.post("/register")
@with_db
async def register(db: AsyncSession, person: PersonCreate):
    existing_email = await db.scalar(select(Person).where(Person.email == person.email))
    if existing_email:
        raise HTTPException(409, "Email already exists")

    new_person = Person(**person.model_dump())
    db.add(new_person)
    await db.commit()
    await notify_application(new_person)

    context = {"name": person.name}
    template = await generate_template(APPLICATION_SUBMITTED_TEMPLATE, context)

    email_request = EmailRequest(
        recipient_email=new_person.email,
        subject=APPLICATION_SUBMITTED_SUBJECT,
        body=template
    )

    await send_email(email_request)
    return person


@router.post("/login")
async def login(request: Request):
    form_data = await request.form()

    redirect_url = form_data.get('state', '/')

    csrf_token_cookie = request.cookies.get('g_csrf_token')
    if not csrf_token_cookie:
        raise HTTPException(400, 'No CSRF token in Cookie.')
    csrf_token_body = form_data.get('g_csrf_token')
    if not csrf_token_body:
        raise HTTPException(400, 'No CSRF token in post body.')
    if csrf_token_cookie != csrf_token_body:
        raise HTTPException(400, 'Failed to verify double submit cookie.')

    token = form_data.get('credential')

    if not token:
        raise HTTPException(401, "No token")

    return await login_user(token, redirect_url)


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
        logger.info(id_info)

        if avatar_url:
            update_req = PersonUpdate(avatar_url=avatar_url)
            await update_person(person.id, update_req)

        access = await create_token(str(person.id))
        refresh = await create_token(str(person.id), expires_in=7*24*60, refresh=True)

        db.add(RefreshToken(token=refresh, person_id=person.id))
        await db.commit()

        response = RedirectResponse(redirect_url, 302)

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


@router.post("/refresh")
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

    await db.delete(stored)

    person_id = payload['person_id']

    new_access = await create_token(str(person_id))
    new_refresh = await create_token(str(person_id), expires_in=7*24*3600, refresh=True)

    db.add(RefreshToken(token=new_refresh, person_id=person_id))

    await db.commit()

    response = RedirectResponse('/', 302)

    response.set_cookie("access_token", new_access, httponly=True,
                        secure=True, samesite="lax", max_age=15*60, path="/")
    response.set_cookie("refresh_token", new_refresh, httponly=True, secure=True,
                        samesite="lax", max_age=7*24*3600, path="/")

    return response


@router.post("/logout")
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
