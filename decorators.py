import os
import jwt
import inspect
from functools import wraps
from typing import TypeVar, Concatenate, Callable, ParamSpec
from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from consts import admins
from db_models import Person
from enums import PersonStatus


auth_secret = os.environ['auth_secret']

P = ParamSpec('P')
T = TypeVar('T')


def with_db(
    func: Callable[Concatenate[AsyncSession, P], T]
) -> Callable[P, T]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        async with get_db() as db:
            return await func(db, *args, **kwargs)

    sig = inspect.signature(func)
    params = list(sig.parameters.values())[1:]
    wrapper.__signature__ = sig.replace(parameters=params)

    return wrapper


@with_db
async def verify_user_token(db: AsyncSession, request: Request):
    token = request.cookies.get("access_token") or \
        request.headers.get("authorization", "").removeprefix("Bearer ")

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
