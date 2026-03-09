import os
import re
import base64
import qrcode
from io import BytesIO
from typing import List
import httpx
from fastapi import Request
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer


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
