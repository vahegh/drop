import os
import re
import json
import base64
import qrcode
from uuid import UUID
from io import BytesIO
from datetime import datetime
from typing import List, Union
import httpx
from fastapi import Request
from pydantic import BaseModel
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from nicegui import ui, app
import secrets
from consts import google_client_id, APP_BASE_URL
import urllib.parse


async def can_share(user_agent):
    if 'firefox' in user_agent or 'fxios' in user_agent:
        return False
    if 'android' in user_agent:
        if 'wv' in user_agent or ('version/' in user_agent and 'chrome/' in user_agent):
            return False
    return True


async def share_event(event):
    user_agent = ui.context.client.request.headers.get("user_agent", "").lower()
    if await can_share(user_agent):
        ui.run_javascript(f'''
            navigator.share({{
                title: {json.dumps(f'{event.name} | Drop Dead Disco')},
                url: {json.dumps(f'{APP_BASE_URL}/event/{event.id}')},
                text: {json.dumps(f'{event.description} Tickets: {APP_BASE_URL}/buy-ticket?event_id={event.id}')}
            }});
        ''')
    else:
        ui.run_javascript(f"await navigator.clipboard.writeText('{APP_BASE_URL}/event/{event.id}')")

    gtag_event("share_event")


async def get_google_auth_url(url='/', login_hint=None):
    csrf_token = secrets.token_urlsafe(32)
    app.storage.user['csrf_token'] = csrf_token

    params = {
        "client_id": google_client_id,
        "redirect_uri": f"{APP_BASE_URL}/google-login",
        "response_type": "code",
        "scope": "openid email profile",
        "hl": "en",
        "state": f"csrf_token={csrf_token}&url={url}",
        "login_hint": login_hint
    }

    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


def gtag_event(event_name, params: dict = {}):
    ui.run_javascript(f"gtag('event', '{event_name}', {json.dumps(params)});")


def fbq_event(event_name, params: dict = None):
    if params:
        ui.run_javascript(f"fbq('track', '{event_name}', {json.dumps(params)});")
    else:
        ui.run_javascript(f"fbq('track', '{event_name}');")


def gtag_config(params: dict = {}):
    ui.run_javascript(f"gtag('config', 'G-152G4X4VLJ', {json.dumps(params)});")


def is_cloud_run():
    return os.getenv("K_SERVICE") is not None


async def get_album_urls(album_url: str) -> List[str]:
    async with httpx.AsyncClient() as client:
        response = await client.get(album_url, follow_redirects=False)
        urls = re.findall(r'https://lh3\.googleusercontent\.com/pw/[A-Za-z0-9_-]+', response.text)
        return list(set(urls))


async def get_user_agent(request: Request):
    user_agent = request.headers.get('user-agent', '').lower()
    if 'android' in user_agent:
        return "android"
    elif 'iphone' in user_agent or 'ipad' in user_agent:
        return "ios"
    else:
        return "web"


def generate_qr(id):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15,
        border=2,
    )
    qr.add_data(id)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(back_color=(255, 255, 255), front_color=(0, 0, 0))
    )

    buffer = BytesIO()
    img.save(buffer, format='PNG')

    return base64.b64encode(buffer.getvalue()).decode('utf-8')


async def parse_inputs(form, model: BaseModel):
    data = {}
    for field_name, element in form.items():
        value = element.value
        field_type = model.model_fields[field_name].annotation
        if field_type is UUID and value:
            value = UUID(value)
        elif field_type is datetime and value:
            value = datetime.fromisoformat(value.replace('T', ' '))
        elif getattr(field_type, '__origin__', None) is Union and datetime in field_type.__args__ and value:
            value = datetime.fromisoformat(value.replace('T', ' '))
        data[field_name] = value

    return data


def get_card_type(bin_6: str) -> str:
    if len(bin_6) < 6:
        return "Unknown"

    first_digit = bin_6[0]
    first_two = bin_6[:2]
    first_four = bin_6[:4]

    if first_digit == '4':
        return "visa"

    if 51 <= int(first_two) <= 55:
        return "mastercard"
    if 2221 <= int(first_four) <= 2720:
        return "mastercard"

    return "Unknown"
