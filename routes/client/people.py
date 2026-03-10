import uuid
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from decorators import verify_user_token
from api_models import PersonCreate, PersonUpdate
from services.person import create_person, update_person, get_person_by_email, get_all_person_stats, delete_person
from services.instagram_check import instagram_check
from services.cloud_storage import upload_avatar

router = APIRouter(tags=["Client People"], prefix="/people")


class InstagramCheckRequest(BaseModel):
    handle: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr


class EmailRequest(BaseModel):
    email: EmailStr


@router.post("", status_code=201)
async def signup(person: PersonCreate):
    return await create_person(person)


@router.get("/stats")
async def person_stats():
    return await get_all_person_stats()


@router.get("/check-email")
async def check_email(email: str):
    person = await get_person_by_email(email)
    if not person:
        return {"exists": False, "status": None, "id": None, "full_name": None}
    return {
        "exists": True,
        "status": person.status,
        "id": str(person.id),
        "full_name": f"{person.first_name} {person.last_name}",
    }


@router.post("/check-instagram")
async def check_instagram(body: InstagramCheckRequest):
    result = await instagram_check(body.handle)
    if not result:
        return JSONResponse({"found": False}, status_code=200)
    return {"found": True, **result}


@router.patch("/me")
async def update_me(body: PersonUpdate, request: Request):
    person = await verify_user_token(request)
    return await update_person(person.id, body)


@router.post("/me/avatar")
async def upload_avatar_endpoint(request: Request, file: UploadFile = File(...)):
    person = await verify_user_token(request)
    file_bytes = await file.read()
    filename = f"{person.id}_{uuid.uuid4().hex[:8]}{_ext(file.filename)}"
    url = await upload_avatar(filename, file_bytes, file.content_type)
    await update_person(person.id, PersonUpdate(avatar_url=url))
    return {"avatar_url": url}


@router.delete("/me/avatar")
async def delete_avatar(request: Request):
    person = await verify_user_token(request)
    await update_person(person.id, PersonUpdate(avatar_url=None))
    return {"ok": True}


@router.post("/me/verify-email")
async def verify_email(body: VerifyEmailRequest, request: Request):
    await verify_user_token(request)
    # OTP email verification – placeholder; wires to existing mailing service when ready
    return {"ok": True}


@router.post("/referral", status_code=201)
async def refer_friend(person: PersonCreate, request: Request):
    await verify_user_token(request)
    if not person.referer_id:
        raise HTTPException(400, "referer_id required")
    return await create_person(person)


@router.post("/unsubscribe")
async def unsubscribe(body: EmailRequest):
    person = await get_person_by_email(body.email)
    if not person:
        raise HTTPException(404, "Person not found")
    print(f"Unsubscribe request received for: {body.email}")
    return {"ok": True}


@router.post("/resubscribe")
async def resubscribe(body: EmailRequest):
    person = await get_person_by_email(body.email)
    if not person:
        raise HTTPException(404, "Person not found")
    print(f"Resubscribe request received for: {body.email}")
    return {"ok": True}


@router.delete("/by-email")
async def delete_by_email(body: EmailRequest, request: Request):
    me = await verify_user_token(request)
    if me.email != body.email:
        raise HTTPException(403, "Forbidden")
    await delete_person(me.id)
    return {"ok": True}


def _ext(filename: str) -> str:
    if "." in filename:
        return "." + filename.rsplit(".", 1)[-1]
    return ""
