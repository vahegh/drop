import os
import re
from typing import List
import httpx
from fastapi import Request


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
