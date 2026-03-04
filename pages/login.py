from uuid import UUID
from nicegui import ui, app
from frame import frame
from components import (section, google_button, primary_button,
                        section_title, rectangular_email_input, outline_button,
                        outline_google_button)
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


@ui.page("/google-login", title="Google Log In | Drop Dead Disco", response_timeout=20)
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


@ui.page("/login", title="Log In | Drop Dead Disco")
async def login_page(token: str = None, redirect_url='/', logged_in=Depends(logged_in)):
    if logged_in:
        ui.navigate.to(redirect_url)
        return

    if token:
        try:
            payload = jwt.decode(token, auth_secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            async with frame():
                with ui.card().classes('gap-4 w-full max-w-96'):
                    section_title("Link expired")
                    primary_button("Try again", target='/login')
                return

        except jwt.InvalidTokenError:
            async with frame():
                with ui.card().classes('gap-4 w-full max-w-96'):
                    section_title("Invalid link")
                    primary_button("Try again", target='/login')
                return

        else:
            person = await get_person_by_email(payload['email'])
            if not person:
                raise HTTPException(404, "No such person - es vonc eq hajoxacrel")
            return await generate_and_set_tokens(person.id)

    async with frame() as f:
        f.classes('px-2 pt-4 min-h-[100svh]')

        with ui.dialog() as dl:
            with ui.card() as c:
                with section("Log in with email link", subtitle="If you are already registered, you can log in using a link sent to your email."):
                    email_input = rectangular_email_input("Verified email")
                    send_link_btn = primary_button("Send link")
                    send_link_btn.on_click(
                        lambda: magic_link(email_input))

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
            else:
                print(f"Person not registered: {email}")

            c.clear()
            with c:
                with section("Check your email!", subtitle="If verified, you'll receive a link to log in."):
                    b = primary_button(
                        "Open Gmail", target="https://mail.google.com", icon="img:/static/images/gmail.svg").on_click(lambda: b.props(add='loading disable'))
            send_link_btn.props(remove='loading disable')

        with ui.card().classes('gap-4 w-full max-w-96 justify-center').props('flat'):
            ui.image(logo_gray_path).classes('w-24 h-8')

            with section("Sign up", subtitle="You must be verified to purchase tickets."):
                google_button("Sign up with Google", redirect_url)

            ui.separator()

            with section("Log In", subtitle="Log in using your verified Google account or a link sent to your email.") as google_login_section:
                outline_google_button("Log in with Google", redirect_url)
                ui.label("OR")
                outline_button("Log in with email link").on_click(dl.open)


@ui.page('/login-as', response_timeout=10)
async def login_as(person_id: UUID):
    try:
        await verify_admin_token(ui.context.client.request)
    except HTTPException:
        async with frame():
            ui.label("Not authorized").classes("text-red-500")
    return await generate_and_set_tokens(person_id=person_id, refresh_expiry=2*60)
