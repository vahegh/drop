import os
import asyncio
import logging
from aiosmtplib import SMTP
from email.message import EmailMessage
from pydantic import BaseModel, EmailStr
from aiosmtplib.errors import SMTPDataError, SMTPServerDisconnected, SMTPException
from consts import APP_BASE_URL, ORG_NAME


logger = logging.getLogger(__name__)

SMTP_SERVER = os.environ['smtp_server']
SMTP_PORT = 587
SENDER_EMAIL = os.environ['smtp_sender_email']
SENDER_FROM = f"{ORG_NAME} <{SENDER_EMAIL}>"
SENDER_PASSWORD = os.environ['smtp_sender_password']
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


class EmailRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    body: str


def create_email_message(email_request: EmailRequest) -> EmailMessage:
    """Create an email message from request."""
    msg = EmailMessage()
    msg["Subject"] = email_request.subject
    msg["From"] = SENDER_FROM
    msg["To"] = email_request.recipient_email
    msg["List-Unsubscribe"] = f"<{APP_BASE_URL}/unsubscribe>, <mailto:{SENDER_EMAIL}?subject=unsubscribe>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.set_content(email_request.body, subtype='html')
    return msg


async def send_email(email_request: EmailRequest):
    """Send a single email with retry logic."""
    msg = create_email_message(email_request)
    await asyncio.sleep(1)

    for attempt in range(MAX_RETRIES):
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

        except (SMTPServerDisconnected, SMTPDataError, SMTPException) as e:
            logger.warning(
                f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {email_request.recipient_email}: {type(e).__name__}: {str(e)}"
            )
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
            else:
                logger.error(
                    f"Failed to send email to {email_request.recipient_email} after {MAX_RETRIES} attempts")
            return

        except Exception as e:
            logger.error(
                f"Unexpected error sending email to {email_request.recipient_email}: {type(e).__name__}: {str(e)}")
            return


async def send_single_email_task(email_request: EmailRequest, semaphore: asyncio.Semaphore) -> tuple[str, bool]:
    """Send a single email with semaphore control."""
    async with semaphore:
        try:
            await send_email(email_request)
            return (email_request.recipient_email, True)
        except Exception as e:
            logger.error(f"Task failed for {email_request.recipient_email}: {str(e)}")
            return (email_request.recipient_email, False)


async def send_bulk_email(email_requests: list[EmailRequest], max_concurrent: int = 10) -> dict[str, int]:
    """
    Send bulk emails with proper concurrency control.

    Args:
        email_requests: List of email requests to send
        max_concurrent: Maximum number of concurrent SMTP connections (default: 10)

    Returns:
        Dictionary with 'success' and 'failed' counts
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    tasks = [
        send_single_email_task(req, semaphore)
        for req in email_requests
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(1 for r in results if isinstance(r, tuple) and r[1])
    failed_count = len(results) - success_count

    logger.info(f"Bulk email complete: {success_count} sent, {failed_count} failed")

    return {
        "success": success_count,
        "failed": failed_count
    }


async def send_bulk_email_batched(
    email_requests: list[EmailRequest],
    batch_size: int = 50,
    max_concurrent: int = 10
) -> dict[str, int]:
    """
    Send bulk emails in batches to avoid overwhelming the SMTP server.

    Args:
        email_requests: List of email requests to send
        batch_size: Number of emails per batch (default: 50)
        max_concurrent: Maximum concurrent connections per batch (default: 10)

    Returns:
        Dictionary with 'success' and 'failed' counts
    """
    total_success = 0
    total_failed = 0

    for email in email_requests:
        result = await send_email(email)
        if result:
            total_success += 1
        else:
            total_failed += 1

    # for i in range(0, len(email_requests), batch_size):
    #     batch = email_requests[i:i + batch_size]
    #     logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} emails")

    #     results = await send_bulk_email(batch, max_concurrent)
    #     total_success += results["success"]
    #     total_failed += results["failed"]

    #     if i + batch_size < len(email_requests):
    #         await asyncio.sleep(1)

    return {
        "success": total_success,
        "failed": total_failed
    }
