from uuid import UUID
from sqlalchemy import select
from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db import with_db
from enums import PersonStatus
from db_models import MemberPass, Person
from services.send_pass import send_member_pass
from services.member_pass import create_member_pass
from api_models import MemberCardCreate, MemberCardResponse

router = APIRouter(tags=['Member Pass'], prefix="/api/member-pass")


@router.get("/all", response_model=list[MemberCardResponse])
@with_db
async def get_all_member_passes(db: AsyncSession):
    passes = await db.scalars(select(MemberPass))
    return passes.all()


@router.get("/person/{person_id}", response_model=MemberCardResponse)
@with_db
async def get_pass_by_person_id(db: AsyncSession, person_id: UUID):
    member_pass = await db.scalar(select(MemberPass).where(MemberPass.person_id == person_id))
    if not member_pass:
        raise HTTPException(404, "Member pass not found")
    return member_pass


@router.get("/{id}", response_model=MemberCardResponse)
@with_db
async def get_pass(db: AsyncSession, id: UUID):
    member_pass = await db.get(MemberPass, id)
    if not member_pass:
        raise HTTPException(404, "Member pass not found")
    return member_pass


@router.post("/", response_model=MemberCardResponse)
@with_db
async def create_pass(db: AsyncSession, member_pass: MemberCardCreate):
    person = await db.get(Person, member_pass.person_id)
    if not person:
        raise HTTPException(404, "Person not found")
    if person.status is not PersonStatus.member:
        raise HTTPException(400, f"Invalid person status: {person.status}")

    member_pass, existing = await create_member_pass(MemberPass(**member_pass.model_dump(mode='json')))
    await send_member_pass(member_pass, resend=bool(existing))

    return member_pass


@router.delete("/{id}")
@with_db
async def delete_pass(db: AsyncSession, id: UUID):
    db_pass = await db.get(MemberPass, id)
    if not db_pass:
        raise HTTPException(404, "Member pass not found")
    await db.delete(db_pass)
    await db.commit()
    return


@router.post("/update-apple-member-pass")
@with_db
async def update_apple_member_pass(db: AsyncSession):
    member_passes = await db.scalars(select(MemberPass))
    for t in member_passes.all():
        await create_member_pass(t)
        print(f"Member pass {t.serial_number} updated.")
