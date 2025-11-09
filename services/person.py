from decorators import with_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db_models import Person
from fastapi import HTTPException


@with_db
async def get_person_by_email(db: AsyncSession, email: str):
    return await db.scalar(select(Person).where(func.lower(Person.email) == email.lower()))
