from nicegui import ui
from frame import frame
from elements import section, large_google_button, primary_button, rectangular_email_input, toast, secondary_button, section_title, accented_button
from fastapi import Request, HTTPException
from consts import logo_black_path, APP_BASE_URL
from services.mailing import EmailRequest, send_email
from services.templating import generate_template
from services.person import get_person_by_email
from services.auth import create_jwt, auth_secret
import jwt
from routes.auth import generate_and_set_tokens
from dependencies import Depends, logged_in


@ui.page('/login')
async def login_page(token: str = None, redirect_url='/', logged_in=Depends(logged_in)):
    if logged_in:
        ui.navigate.to('/profile')
        return

    if token:
        try:
            payload = jwt.decode(token, auth_secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            async with frame(show_footer=False):
                with ui.card().classes('gap-4 w-full max-w-96'):
                    section_title("Magic link expired")
                    primary_button("Try again").on_click(lambda: ui.navigate.to('/login'))
                return

        except jwt.InvalidTokenError:
            async with frame(show_footer=False):
                with ui.card().classes('gap-4 w-full max-w-96'):
                    section_title("Invalid magic link")
                    primary_button("Try again").on_click(lambda: ui.navigate.to('/login'))
                return

        else:
            person = await get_person_by_email(payload['email'])
            if not person:
                raise HTTPException(404, "No such person - es vonc eq hajoxacrel")
            return await generate_and_set_tokens(person.id)

    async with frame(show_footer=False) as f:
        f.classes('px-2')

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
                subject="Your signin link",
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

        with ui.card().classes('gap-4 w-full max-w-96 justify-center') as main_card:
            ui.image(logo_black_path).classes('w-24 h-8')

            with section() as google_login_section:
                section_title("Login or sign up with Google")
                large_google_button(redirect_url)
                ui.label("OR")
                primary_button("Login using magic link").on_click(toggle_login)

            with section('Login with magic link') as link_login_section:
                link_login_section.set_visibility(False)
                email_input = rectangular_email_input("Verified email")
                send_link_btn = primary_button('Send link')
                send_link_btn.on_click(
                    lambda: magic_link(email_input))
                accented_button("Login with Google").on_click(toggle_login)
