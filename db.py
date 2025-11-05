import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import asynccontextmanager, contextmanager
from typing import TypeVar, Concatenate, overload, Callable, ParamSpec
from functools import wraps
import inspect

db_conn_string = os.environ["db_conn_string"]


engine = create_async_engine(
    db_conn_string,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,

)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_db():
    db = SessionLocal()  # or however you create your async session
    try:
        yield db
    finally:
        await db.close()


P = ParamSpec('P')
T = TypeVar('T')


def with_db(
    func: Callable[Concatenate[AsyncSession, P], T]
) -> Callable[P, T]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        async with get_db() as db:
            return await func(db, *args, **kwargs)

    # Remove db from signature for FastAPI
    sig = inspect.signature(func)
    params = list(sig.parameters.values())[1:]
    wrapper.__signature__ = sig.replace(parameters=params)

    return wrapper
