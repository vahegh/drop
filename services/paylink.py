import os
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db import engine
from db_models import Payment

PAYLINK_API_BASE_URL = os.getenv("PAYLINK_API_BASE_URL")
PAYLINK_PARTNER_ID = os.getenv("PAYLINK_PARTNER_ID")
PAYLINK_PARTNER_KEY = os.getenv("PAYLINK_PARTNER_KEY")
PAYLINK_BACK_URL = "https://dropdeadisco.com/success"


async def get_paylink_token() -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYLINK_API_BASE_URL}/api/authorization/authorize",
            json={"partnerId": PAYLINK_PARTNER_ID, "partnerKey": PAYLINK_PARTNER_KEY},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        return data["accessToken"]["token"]


async def generate_payment_link(name: str, amount: float, person_id, person_name, event_id) -> str:
    async with AsyncSession(engine) as db:
        existing = await db.scalar(select(Payment).where((Payment.event_id == event_id) & (Payment.person_id == person_id)))
        if existing:
            return existing.pay_url

    token = await get_paylink_token()

    payload = {
        "requestType": f"{name} Event Ticket",
        "requestInfo": person_name,
        "amount": amount,
        "isFlexible": False,
        "allowAnonymous": True,
        "isActive": True,
        "maxCount": 1,
        "language": "en"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYLINK_API_BASE_URL}/api/request/register",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        data = response.json()
        payment = Payment(
            person_id=person_id,
            event_id=event_id,
            request_id=data['requestId'],
            pay_url=data['redirectUrl']
        )
        async with AsyncSession(engine) as db:
            db.add(payment)
            await db.commit()
        print("Payment link generated")
        return data['redirectUrl']
