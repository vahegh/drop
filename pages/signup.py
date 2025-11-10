import jwt
from nicegui import ui
from frame import frame
from elements import (rectangular_email_input, instagram_input, accented_button,
                      name_input, section, primary_button, section_title)
from api_models import PersonCreate

from fastapi import HTTPException
from routes.auth import register
from services.instagram_check import instagram_check
from consts import logo_black_path


@ui.page('/signup')
async def signup_page(token):
    try:
        token_info = jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
    except jwt.DecodeError:
        raise HTTPException(401, "Invalid token")

    async with frame(show_footer=False) as main_col:
        main_col.classes('bg-gray-100 p-2')
        main_card = ui.card().classes('gap-4 w-full max-w-96')

        with main_card:
            with section():
                ui.image(logo_black_path).classes('w-24')

                with ui.column().classes('w-full gap-0 items-center'):
                    section_title("Sign up")

                    ui.markdown("""Welcome to Drop Dead Disco! 
                                Before we proceed, we need your **Instagram profile** for review. This is a one-time process.""").classes('text-sm text-gray-700 text-center')

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
                    btn.props(add='loading disable')
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

                    instagram_info = await instagram_check(insta)

                    with ui.dialog() as dl:
                        with ui.card().classes('gap-4 w-full max-w-96'):
                            if instagram_info:
                                with section():
                                    ui.link(
                                        f"@{insta}", f"https://instagram.com/{insta}").classes('text-2xl')
                                    ui.label(f"{instagram_info['followers']} followers").classes(
                                        'text-gray-600')

                                with section():
                                    section_title("Is this you?")
                                    with ui.row(wrap=False):
                                        primary_button("No").on_click(lambda: dl.submit(False))
                                        accented_button("Yes, submit").on_click(
                                            lambda: dl.submit(True))
                            else:
                                with section(f"Instagram user {insta} not found", subtitle="Please check your username."):
                                    primary_button("Fix").on_click(lambda: (dl.submit(False)))

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
