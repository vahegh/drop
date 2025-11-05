import base64
from email.message import EmailMessage

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from services.google_auth import credentials

SENDER_EMAIL = os.environ['sender_email']


async def gmail_send_message(to, subject, body):

    try:
        service = build("gmail", "v1", credentials=credentials)
        message = EmailMessage()

        message.set_content(body)

        message["To"] = to
        message["From"] = SENDER_EMAIL
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        send_message = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": encoded_message})
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None
    return send_message
