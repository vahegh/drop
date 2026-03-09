import os
from sqlalchemy import select
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from decorators import with_db
from decorators import verify_user_token
from db_models import RefreshToken
from sqlalchemy.ext.asyncio import AsyncSession
from services.user import user_info
from services.person import create_person, get_person_by_email
from api_models import PersonCreate
from routes.auth import generate_and_set_tokens

aud = os.environ['google_client_id']

router = APIRouter(tags=["Client Auth"], prefix="/auth")


class GoogleAuthRequest(BaseModel):
    credential: str


class SignupRequest(BaseModel):
    credential: str
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
    try:
        info = id_token.verify_oauth2_token(
            body.credential, google_requests.Request(), aud, clock_skew_in_seconds=5)
    except ValueError:
        raise HTTPException(401, "Invalid Google token")

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


@router.post("/signup")
async def signup_react(body: SignupRequest):
    try:
        info = id_token.verify_oauth2_token(
            body.credential, google_requests.Request(), aud, clock_skew_in_seconds=5)
    except ValueError:
        raise HTTPException(401, "Invalid Google token")

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
