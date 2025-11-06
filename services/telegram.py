import os
import httpx
import logging
from db_models import Person, Payment
from api_models import TelegramMessage


logger = logging.getLogger(__name__)

telegram_chat_id_payments = "-4934132606"
telegram_chat_id = os.environ["telegram_chat_id"]
telegram_bot_token = os.environ["telegram_bot_token"]
telegram_api_url = f"https://api.telegram.org/bot{telegram_bot_token}"


async def notify_application(person: Person):
    text = f"""<b>New application!</b>
    <b>Name:</b> {person.name}
    <b>Email:</b> {person.email}
    <b>Instagram:</b> <a href='https://www.instagram.com/{person.instagram_handle}'>@{person.instagram_handle}</a>"""
    reply_markup = {
        'inline_keyboard': [[
            {'text': 'Approve', 'callback_data': f'verified_{person.id}'},
            {'text': 'Reject', 'callback_data': f'rejected_{person.id}'},
            {'text': 'Member', 'callback_data': f'member_{person.id}'},
        ]]
    }
    tg_message = TelegramMessage(
        chat_id=telegram_chat_id,
        text=text,
        reply_markup=reply_markup)
    await send_tg_message(tg_message)


async def notify_payment_page_view(person: Person):
    text = f"""<b>New payment page view!</b>
    <b>Name:</b> {person.name}
    <b>Instagram:</b> <a href='https://www.instagram.com/{person.instagram_handle}'>@{person.instagram_handle}</a>"""
    tg_message = TelegramMessage(
        chat_id=telegram_chat_id_payments,
        text=text)
    await send_tg_message(tg_message)


async def notify_payment_init(person: Person, payment: Payment, recipients: list[str]):
    text = f"""<b>Payment initialized!</b>
    <b>Name:</b> {person.name}
    <b>Instagram:</b> <a href='https://www.instagram.com/{person.instagram_handle}'>@{person.instagram_handle}</a>
    <b>Amount: {int(payment.amount)} AMD</b>
    <b>Provider:</b> {payment.provider.value}
    <b>Recipients:</b> {','.join(recipients)}"""

    tg_message = TelegramMessage(
        chat_id=telegram_chat_id_payments,
        text=text)
    await send_tg_message(tg_message)


async def notify_payment_confirmed(person: Person, payment: Payment, recipients: list[str]):
    text = f"""<b>Payment confirmed!</b>
    <b>Name:</b> {person.name}
    <b>Instagram:</b> <a href='https://www.instagram.com/{person.instagram_handle}'>@{person.instagram_handle}</a>
    <b>Amount: {int(payment.amount)} AMD</b>
    <b>Provider:</b> {payment.provider.value}
    <b>Recipients:</b> {','.join(recipients)}"""

    tg_message = TelegramMessage(
        chat_id=telegram_chat_id_payments,
        text=text)
    await send_tg_message(tg_message)


async def send_tg_message(message: TelegramMessage):
    payload = message.model_dump(mode='json', exclude_none=True)
    url = f"{telegram_api_url}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Failed to send Telegram message")
        logger.error(e.response.json())
    else:
        logger.info("Successfully sent Telegram message")
