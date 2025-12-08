import jwt
from nicegui import ui
from frame import frame
from components import (rectangular_email_input, instagram_input, accented_button,
                        name_input, section, primary_button, section_title, instagram_dialog)
from api_models import PersonCreate

from fastapi import HTTPException
from routes.auth import register
from services.instagram_check import instagram_check
from consts import logo_gray_path


@ui.page('/signup')
async def signup_page(token):
    try:
        token_info = jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
    except jwt.DecodeError:
        raise HTTPException(401, "Invalid token")

    async with frame() as main_col:
        main_col.classes('px-2 pt-4 min-h-[100svh]')
        main_card = ui.card().classes('gap-4 w-full max-w-96').props('flat')

        with main_card:
            ui.image(logo_gray_path).classes('w-24 h-8')

            with section() as s:
                s.classes('h-[480px]')
                with ui.column().classes('w-full gap-0 items-center'):
                    section_title("Sign up")

                    ui.markdown("""Welcome to Drop Dead Disco! 
                                Before we proceed, we need your **Instagram profile** for review. This is a one-time process.""").classes('text-sm text-gray-500 text-center')

                with ui.column().classes('w-full gap-0'):
                    firstname_input = name_input(
                        "First name", "John", value=token_info.get('given_name', ''))
                    lastname_input = name_input(
                        "Last name", "Doe", value=token_info.get('family_name', ''))
                    email_input = rectangular_email_input(
                        value=token_info.get('email', '')).props(add='readonly')
                    insta_input = instagram_input()

                btn = accented_button('Submit')

                async def submit():
                    if not all([
                        firstname_input.validate(),
                        lastname_input.validate(),
                        email_input.validate(),
                        insta_input.validate()
                    ]):
                        return
                    btn.props(add='loading disable')

                    first_name = firstname_input.value.strip()
                    last_name = lastname_input.value.strip()
                    email = email_input.value.strip()
                    insta = insta_input.value.strip().lstrip('@')

                    instagram_info = await instagram_check(insta)

                    dl = instagram_dialog(instagram_info)

                    dl.open()

                    result = await dl

                    if result:
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
                    dl.delete()
                    btn.props(remove='loading disable')

                btn.on_click(submit)
