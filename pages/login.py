from uuid import UUID
from nicegui import ui, app
from frame import frame
from components import (section, google_button, primary_button,
                        section_title, rectangular_email_input, outline_button)
from fastapi import Request, HTTPException
from consts import logo_gray_path, APP_BASE_URL, google_client_id
from services.mailing import EmailRequest, send_email
from services.templating import generate_template
from services.person import get_person_by_email
from services.auth import create_jwt, auth_secret
import jwt
import os
from routes.auth import generate_and_set_tokens
from dependencies import Depends, logged_in
from routes.auth import login_user
import urllib.parse
import httpx
from decorators import verify_admin_token

client_secret = os.environ['google_client_secret']


@ui.page("/google-login", response_timeout=20)
async def google_login(request: Request):
    state_parts = urllib.parse.parse_qs(request.query_params.get('state', ''))
    cstf_token = state_parts.get('csrf_token', [None])[0]
    redirect_url = state_parts.get('url', [None])[0]

    if cstf_token != app.storage.user.get('csrf_token'):
        raise HTTPException(401, "Invalid request - CSRF token doesnt match")

    app.storage.user.clear()

    code = request.query_params.get("code")
    async with httpx.AsyncClient() as client:
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": google_client_id,
            "client_secret": client_secret,
            "redirect_uri": f"{APP_BASE_URL}/google-login",
            "grant_type": "authorization_code",
        }
        resp = await client.post(token_url, data=token_data)
        token = resp.json().get("id_token")
        if not token:
            raise HTTPException(401, "No id token")

        return await login_user(token, redirect_url)


@ui.page('/login')
async def login_page(token: str = None, redirect_url='/', logged_in=Depends(logged_in)):
    if logged_in:
        ui.navigate.to('/profile')
        return

    if token:
        try:
            payload = jwt.decode(token, auth_secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            async with frame():
                with ui.card().classes('gap-4 w-full max-w-96'):
                    section_title("Magic link expired")
                    primary_button("Try again").on_click(lambda: ui.navigate.to('/login'))
                return

        except jwt.InvalidTokenError:
            async with frame():
                with ui.card().classes('gap-4 w-full max-w-96'):
                    section_title("Invalid magic link")
                    primary_button("Try again").on_click(lambda: ui.navigate.to('/login'))
                return

        else:
            person = await get_person_by_email(payload['email'])
            if not person:
                raise HTTPException(404, "No such person - es vonc eq hajoxacrel")
            return await generate_and_set_tokens(person.id)

    async with frame() as f:
        f.classes('px-2 pt-4 min-h-[100svh]')

        async def magic_link(email_input):
            if not email_input.validate():
                return

            send_link_btn.props(add='loading disable')

            email = email_input.value

            person = await get_person_by_email(email)

            if person:
                jwt = await create_jwt(person.email)

            context = {"name": person.first_name,
                       "magic_link": f"{APP_BASE_URL}/login?token={jwt}"}
            template = await generate_template("magic_link.html", context)
            outgoing_email = EmailRequest(
                recipient_email=email,
                subject="Your Signin Link",
                body=template
            )
            await send_email(outgoing_email)

            with main_card:
                main_card.clear()
                with section("Check your email!", subtitle="If verified, you'll receive a link to log in."):
                    pass

        async def toggle_login() -> None:
            google_login_section.set_visibility(not google_login_section.visible)
            link_login_section.set_visibility(not link_login_section.visible)

        with ui.card().classes('gap-4 w-full max-w-96 justify-center').props('flat') as main_card:
            ui.image(logo_gray_path).classes('w-24 h-8')

            with section() as google_login_section:
                section_title("Login or sign up")
                google_button("Continue with Google", redirect_url)
                ui.label("OR")
                outline_button("Login using magic link").on_click(toggle_login)

            with section('Login with magic link') as link_login_section:
                link_login_section.set_visibility(False)
                email_input = rectangular_email_input("Verified email")
                send_link_btn = outline_button('Send link')
                send_link_btn.on_click(
                    lambda: magic_link(email_input))
                google_button("Continue with Google", redirect_url)


@ui.page('/login-as')
async def login_as(person_id: UUID):
    try:
        await verify_admin_token(ui.context.client.request)
    except HTTPException:
        async with frame():
            ui.label("Not authorized").classes("text-red-500")
    return await generate_and_set_tokens(person_id=person_id, refresh_expiry=2*60)
