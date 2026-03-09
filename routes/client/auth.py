import os
import jwt as pyjwt
import httpx
from sqlalchemy import select
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from decorators import with_db
from decorators import verify_user_token
from db_models import RefreshToken
from sqlalchemy.ext.asyncio import AsyncSession
from services.user import user_info
from services.person import create_person, get_person_by_email
from services.auth import create_jwt, auth_secret
from services.mailing import EmailRequest, send_email
from services.templating import generate_template
from api_models import PersonCreate
from routes.auth import generate_and_set_tokens
from consts import APP_BASE_URL

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


async def _get_google_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise HTTPException(401, "Invalid Google access token")
    return resp.json()

router = APIRouter(tags=["Client Auth"], prefix="/auth")


class GoogleAuthRequest(BaseModel):
    access_token: str


class SignupRequest(BaseModel):
    access_token: str
    first_name: str
    last_name: str
    instagram_handle: str


@router.get("/me")
async def me(request: Request):
    return await user_info(request)


@router.post("/logout")
@with_db
async def logout(db: AsyncSession, request: Request):
    token = request.cookies.get("refresh_token")

    response = JSONResponse({"ok": True})
    response.delete_cookie("access_token", secure=True, httponly=True, samesite="lax")
    response.delete_cookie("refresh_token", secure=True, httponly=True, samesite="lax")

    if token:
        stored = await db.scalar(select(RefreshToken).where(RefreshToken.token == token))
        if stored:
            await db.delete(stored)
            await db.commit()

    return response


@router.post("/google")
async def google_auth(body: GoogleAuthRequest):
    info = await _get_google_userinfo(body.access_token)
    email = info['email']
    person = await get_person_by_email(email)

    if not person:
        return JSONResponse({
            "status": "new_user",
            "email": email,
            "first_name": info.get("given_name", ""),
            "last_name": info.get("family_name", ""),
            "avatar_url": info.get("picture"),
        })

    if person.status == 'rejected':
        raise HTTPException(403, "Account rejected")

    redirect_resp = await generate_and_set_tokens(person.id, redirect_url="/")
    json_resp = JSONResponse({"status": "ok"})
    for key, val in redirect_resp.raw_headers:
        if key == b"set-cookie":
            json_resp.raw_headers.append((key, val))
    return json_resp


class MagicLinkRequest(BaseModel):
    email: str


@router.post("/magic-link")
async def send_magic_link(body: MagicLinkRequest):
    person = await get_person_by_email(body.email)
    if person:
        token = await create_jwt(person.email, expires_in=30)
        context = {
            "name": person.first_name,
            "magic_link": f"{APP_BASE_URL}/login?token={token}",
        }
        template = await generate_template("magic_link.html", context)
        await send_email(EmailRequest(
            recipient_email=body.email,
            subject="Your Signin Link",
            body=template,
        ))
    return JSONResponse({"status": "ok"})


@router.get("/magic-link/verify")
async def verify_magic_link(token: str):
    try:
        payload = pyjwt.decode(token, auth_secret, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(401, "Link expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(401, "Invalid link")

    person = await get_person_by_email(payload["email"])
    if not person:
        raise HTTPException(404, "Person not found")

    if person.status == 'rejected':
        raise HTTPException(403, "Account rejected")

    return await generate_and_set_tokens(person.id, redirect_url="/")


@router.post("/signup")
async def signup_react(body: SignupRequest):
    info = await _get_google_userinfo(body.access_token)

    person = await create_person(PersonCreate(
        first_name=body.first_name,
        last_name=body.last_name,
        email=info['email'],
        instagram_handle=body.instagram_handle,
        avatar_url=info.get("picture"),
    ))
    if not person:
        raise HTTPException(400, "Signup failed")

    redirect_resp = await generate_and_set_tokens(person.id, redirect_url="/")
    json_resp = JSONResponse({"status": "ok"})
    for key, val in redirect_resp.raw_headers:
        if key == b"set-cookie":
            json_resp.raw_headers.append((key, val))
    return json_resp
