import jwt
from nicegui import ui
from frame import frame
from elements import (rectangular_email_input, instagram_input,
                      page_header, accented_button, name_input)
from api_models import PersonCreate

from fastapi import HTTPException
from routes.auth import register


@ui.page('/signup')
async def signup_page(token):
    try:
        token_info = jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
    except jwt.DecodeError:
        raise HTTPException(401, "Invalid token")

    async with frame() as main_col:
        main_col.classes(add='p-4 justify-between gap-4')
        page_header("Sign up")
        ui.label("Welcome to Drop Dead Disco! Before we proceed, we need your Instagram profile for review. This is a one-time process.  "
                 "Please fill it in below:").classes('text-sm/6 px-3 text-gray-700')
        with ui.column().classes('w-full gap-0'):
            firstname_input = name_input(
                "First name", "John", value=token_info.get('given_name', ''))
            lastname_input = name_input(
                "Last name", "Doe", value=token_info.get('family_name', ''))
            email_input = rectangular_email_input(value=token_info.get('email', ''))
            insta_input = instagram_input()

        async def submit():
            if not all([
                firstname_input.validate(),
                lastname_input.validate(),
                email_input.validate(),
                insta_input.validate()
            ]):
                return

            first_name = firstname_input.value.strip()
            last_name = lastname_input.value.strip()
            email = email_input.value.strip()
            insta = insta_input.value.strip().lstrip('@')

            btn.props(add='loading')

            payload = PersonCreate(
                first_name=first_name,
                last_name=last_name,
                email=email,
                instagram_handle=insta,
                avatar_url=token_info['picture']
            )

            print(payload.model_dump())

            person = await register(payload)

            if person:
                ui.navigate.to(f'/api/auth/login-user?token={token}')

            else:
                main_col.clear()
                with main_col:
                    with ui.column().classes('p-8 fixed inset-0 h-svh'):
                        ui.label("Unknown error occured.").classes(
                            'text-5xl font-bold')
                        ui.label(
                            "Please try again a little later.").classes('text-xl')

        btn = accented_button('Submit').on_click(submit)
