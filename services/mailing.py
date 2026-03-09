import os
# import asyncio
import logging
from aiosmtplib import SMTP
from email.message import EmailMessage
from pydantic import BaseModel, EmailStr
# from aiosmtplib.errors import SMTPDataError, SMTPServerDisconnected, SMTPException
from consts import APP_BASE_URL, ORG_NAME


logger = logging.getLogger(__name__)

SMTP_SERVER = os.environ['smtp_server']
SMTP_PORT = 587
SENDER_EMAIL = os.environ['smtp_sender_email']
SENDER_FROM = f"{ORG_NAME} <{SENDER_EMAIL}>"
SENDER_PASSWORD = os.environ['smtp_sender_password']
# MAX_RETRIES = 3
# RETRY_DELAY = 2


class EmailRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    body: str
    transactional: bool = True


def create_email_message(email_request: EmailRequest):
    msg = EmailMessage()
    msg["Subject"] = email_request.subject
    msg["From"] = SENDER_FROM
    msg["To"] = email_request.recipient_email
    if not email_request.transactional:
        msg["List-Unsubscribe"] = f"<{APP_BASE_URL}/app/unsubscribe>, <mailto:{SENDER_EMAIL}?subject=unsubscribe>"
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.set_content(email_request.body, subtype='html')
    return msg


async def send_email(email_request: EmailRequest):
    msg = create_email_message(email_request)

    smtp_client = SMTP(
        hostname=SMTP_SERVER,
        port=SMTP_PORT,
        start_tls=True,
        username=SENDER_EMAIL,
        password=SENDER_PASSWORD,
        timeout=30.0
    )

    try:
        async with smtp_client as client:
            await client.send_message(msg)
        logger.info(f"Email sent successfully to {email_request.recipient_email}")
        return True

    except Exception as e:
        logger.error(
            f"Failed to send email to {email_request.recipient_email}: {type(e).__name__}: {str(e)}")
        return False
