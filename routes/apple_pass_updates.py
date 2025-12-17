from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException, Request, Response
from decorators import with_db
from services.cloud_storage import get_pass_file
from services.apple_pass import APPLE_PASS_TYPE_ID, APPLE_AUTH_TOKEN
from api_models import RegistrationRequest, UpdatedPassesResponse, LogRequest
from db_models import AppleDevices, AppleDeviceRegistrations, EventTicket, MemberPass
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=['Apple Pass Updates'], prefix="/api/passupdates/v1")


@router.post("/devices/{device_id}/registrations/{pass_type_id}/{serial_number}", status_code=201)
@with_db
async def register_device(
    db: AsyncSession,
    device_id: str,
    pass_type_id: str,
    serial_number: str,
    request: Request,
    body: RegistrationRequest,

):
    if pass_type_id != APPLE_PASS_TYPE_ID:
        raise HTTPException(400, "Invalid pass type ID")
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"ApplePass {APPLE_AUTH_TOKEN}":
        raise HTTPException(401, "Unauthorized")

    pass_exists = await db.get(EventTicket, serial_number) or await db.get(MemberPass, serial_number)

    if not pass_exists:
        raise HTTPException(404, "Pass not found")

    existing_registration = await db.scalar(
        select(AppleDeviceRegistrations).where(
            AppleDeviceRegistrations.device_id == device_id,
            AppleDeviceRegistrations.pass_type_id == pass_type_id,
            AppleDeviceRegistrations.serial_number == serial_number
        )
    )
    if existing_registration:
        return Response(status_code=200)

    await db.execute(
        insert(AppleDevices).values(
            device_id=device_id,
            push_token=body.pushToken
        ).on_conflict_do_update(
            constraint="apple_devices_pkey",
            set_={"push_token": body.pushToken}
        )
    )
    await db.execute(
        insert(AppleDeviceRegistrations).values(
            device_id=device_id,
            pass_type_id=pass_type_id,
            serial_number=serial_number
        ).on_conflict_do_nothing()
    )
    await db.commit()

    return Response(status_code=201)


@router.delete("/devices/{device_id}/registrations/{pass_type_id}/{serial_number}")
@with_db
async def unregister_device(
    db: AsyncSession,
    device_id: str,
    pass_type_id: str,
    serial_number: str,
    request: Request,

):
    if pass_type_id != APPLE_PASS_TYPE_ID:
        raise HTTPException(400, "Invalid pass type ID")
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"ApplePass {APPLE_AUTH_TOKEN}":
        raise HTTPException(401, "Unauthorized")

    result = await db.execute(
        delete(AppleDeviceRegistrations).where(
            AppleDeviceRegistrations.device_id == device_id,
            AppleDeviceRegistrations.pass_type_id == pass_type_id,
            AppleDeviceRegistrations.serial_number == serial_number
        )
    )
    if result.rowcount == 0:
        raise HTTPException(404, "Registration not found")

    remaining_registrations = await db.scalar(
        select(AppleDeviceRegistrations).where(
            AppleDeviceRegistrations.device_id == device_id).exists().select()
    )
    if not remaining_registrations:
        await db.execute(
            delete(AppleDevices).where(AppleDevices.device_id == device_id)
        )

    await db.commit()
    return Response(status_code=200)


@router.get("/devices/{device_id}/registrations/{pass_type_id}")
@with_db
async def get_updated_passes(
    db: AsyncSession,
    device_id: str,
    pass_type_id: str,

):
    if pass_type_id != APPLE_PASS_TYPE_ID:
        raise HTTPException(400, "Invalid pass type ID")

    registrations = await db.execute(
        select(AppleDeviceRegistrations.serial_number).where(
            AppleDeviceRegistrations.device_id == device_id,
            AppleDeviceRegistrations.pass_type_id == pass_type_id
        )
    )
    serial_numbers = [row[0] for row in registrations.fetchall()]
    if not serial_numbers:
        return Response(status_code=204)

    return UpdatedPassesResponse(
        serialNumbers=serial_numbers,
        lastUpdated=datetime.now(timezone.utc).isoformat()
    )


@router.get("/passes/{pass_type_id}/{serial_number}")
@with_db
async def get_updated_pass(
    db: AsyncSession,
    pass_type_id: str,
    serial_number: str,

):
    if pass_type_id != APPLE_PASS_TYPE_ID:
        raise HTTPException(400, "Invalid pass type ID")

    pass_record = await db.get(EventTicket, serial_number) or await db.get(MemberPass, serial_number)

    if not pass_record:
        raise HTTPException(404, "Pass not found")

    passfile = await get_pass_file(serial_number)
    if not passfile:
        raise HTTPException(404, "Pass file not found")

    return StreamingResponse(
        iter([passfile]),
        media_type="application/vnd.apple.pkpass",
        headers={"Last-Modified": pass_record.updated_at.strftime("%a, %d %b %Y %H:%M:%S GMT")}
    )


@router.post("/log")
async def log(body: LogRequest):
    logger.info(body.logs)
    return {"status": "success"}
