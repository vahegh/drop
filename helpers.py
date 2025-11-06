import httpx
import re
import os
from api_models import *
from typing import List, Union
from nicegui import ui
import base64
from nicegui import app
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from io import BytesIO
from fastapi import HTTPException, Request
from routes.user import user_info, modify_user
from routes.auth import login, logout, refresh


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


async def set_user_data(request: Request):
    person = None
    if request.cookies.get('access_token'):
        try:
            person = await user_info(request)
        except HTTPException:
            if request.cookies.get('refresh_token'):
                try:
                    await refresh(request)
                except HTTPException:
                    return False
                else:
                    person = await user_info(request)
            else:
                return False
    else:
        if request.cookies.get('refresh_token'):
            try:
                await refresh(request)
            except HTTPException as e:
                ui.navigate.to('/logout')
            else:
                person = await user_info(request)
        else:
            return False

    if person:
        if not person.avatar_url:
            avatar_url = app.storage.user.get('avatar_url')
            if avatar_url:
                try:
                    person = await modify_user(PersonUpdate(avatar_url=avatar_url), request)
                except HTTPException as e:
                    return False

        app.storage.user.update(person.model_dump(mode='json'))
        return True


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
