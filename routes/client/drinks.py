from fastapi import APIRouter
from services.drink import get_all_drinks

router = APIRouter(tags=["Client Drinks"], prefix="/drinks")


@router.get("")
async def list_drinks():
    return await get_all_drinks()
