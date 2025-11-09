import httpx
from fastapi.responses import Response
from fastapi import APIRouter, Request
from db_models import Person
from api_models import PersonUpdate, PersonResponse
from routes.person import update_person
from services.telegram import telegram_api_url, notify_payment_page_view

router = APIRouter(tags=['Telegram Webhook'], prefix="/api/telegram")


@router.post("/webhook/")
async def webhook(request: Request):
    update = await request.json()

    if "callback_query" in update:
        query = update["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        message_id = query["message"]["message_id"]
        callback_data = query["data"]
        query_id = query["id"]

        status, person_id = callback_data.split("_")
        person = PersonUpdate(status=status)

        db_person = await update_person(person_id, person)

        message = (
            f"<b>First name:</b> {person.first_name}\n"
            f"<b>Last name:</b> {person.last_name}\n"
            f"<b>Email:</b> {db_person.email}\n"
            f"<b>Instagram:</b> <a href='https://www.instagram.com/{db_person.instagram_handle}'>@{db_person.instagram_handle}</a>\n"
            f"Status: {status}."
        )

        async with httpx.AsyncClient() as client:
            await client.post(f"{telegram_api_url}/editMessageText", json={
                "chat_id": chat_id,
                "message_id": message_id,
                'parse_mode': 'HTML',
                "text": message,
                'reply_markup': {}
            })

            await client.post(f"{telegram_api_url}/answerCallbackQuery", json={
                "callback_query_id": query_id
            })

    return Response(status_code=200)


async def payment_page_view(person: PersonResponse):
    await notify_payment_page_view(Person(**person.model_dump()))
