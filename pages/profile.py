from nicegui import ui, app
from consts import APP_BASE_URL, name_validation, email_validation, insta_validation
from elements import (primary_button, secondary_button, status_icon,
                      page_header, section, toast, instagram_dialog)
from services.person import update_person, get_person_by_email
from api_models import PersonResponseFull, PersonUpdate
from frame import frame
from dependencies import logged_in, Depends
from fastapi import Request
from services.instagram_check import instagram_check
import random
from services.mailing import EmailRequest, send_email
from services.templating import generate_template


@ui.page('/profile', title='Drop Dead Disco')
async def home_page(request: Request, logged_in=Depends(logged_in)):

    async with frame(show_footer=False) as f:
        f.classes('py-14')
        if not logged_in:
            ui.navigate.to(f'/login?redirect_url={APP_BASE_URL}/profile')
            return

        person: PersonResponseFull = request.state.person
        ui.context.client.page.title = f"{person.first_name}'s profile | Drop Dead Disco"

        async def modify_fn(first_name):
            if not first_name.validate():
                return
            try:
                await update_person(person.id, PersonUpdate(first_name=first_name.value))
            except Exception as e:
                toast(f"Unable to save first name: {str(e)}")
            else:
                toast(f"Updated first name to {first_name.value}.")

        async def modify_ln(last_name):
            if not last_name.validate():
                return
            try:
                await update_person(person.id, PersonUpdate(last_name=last_name.value))
            except Exception as e:
                toast(f"Unable to save last name: {str(e)}")
            else:
                toast(f"Updated last name to {last_name.value}.")

        async def modify_instagram(username):
            if not username.validate():
                return
            instagram_info = await instagram_check(username.value)
            dl = instagram_dialog(instagram_info)
            dl.open()
            result = await dl
            if result:
                try:
                    await update_person(person.id, PersonUpdate(instagram_handle=instagram.value))
                except Exception as e:
                    toast(f"Unable to save Instagram username: {str(e)}")
                else:
                    toast(f"Updated Instagram username to {instagram.value}.")
            dl.delete()

        async def send_otp(new_email):
            otp = random.randint(100000, 999999)
            app.storage.user['otp'] = str(otp)
            context = {"name": person.first_name, "otp": otp}
            template = await generate_template("otp.html", context=context)
            outgoing_email = EmailRequest(
                recipient_email=new_email,
                subject="One-time verification code",
                body=template
            )
            await send_email(outgoing_email)

        async def modify_email(new_email):
            if not new_email.validate():
                return

            async def verify_otp(otp):
                dl.submit(otp == app.storage.user['otp'])

            existing_user = await get_person_by_email(new_email.value)
            if existing_user:
                toast("This email is already used.", type='warning')
                return

            with ui.dialog(value=True) as dl:
                with ui.card().classes('w-full'):
                    with section("Verify email", subtitle="Send a one-time code to your new email to verify."):

                        otp_input = ui.input("OTP")
                        otp_input.set_visibility(False)

                        save_btn = secondary_button("Verify").on_click(
                            lambda: verify_otp(otp_input.value))
                        save_btn.set_visibility(False)

                        send_btn = primary_button("Send OTP").on_click(
                            lambda: send_otp(new_email.value))

                        send_btn.on_click(lambda: (send_btn.set_text(
                            "Send again"), save_btn.set_visibility(True), otp_input.set_visibility(True)))

            result = await dl

            if result:
                try:
                    await update_person(person.id, PersonUpdate(email=email.value))
                except Exception as e:
                    toast(f"Unable to save email: {str(e)}")
                else:
                    toast(f"Updated email to {email.value}.")

        with section():
            if person.avatar_url:
                ui.image(person.avatar_url).classes('size-20 rounded-full')
            else:
                ui.icon('account_circle', size='80px')

            page_header(f'{person.first_name} {person.last_name}')
            status_icon(person.status)

        with section("Your profile"):
            async def editable_field(label: str, value: str, validation):
                with ui.row().classes('w-full items-end gap-2'):
                    input_field = ui.input(label=label, value=value,
                                           validation=validation).props('readonly')
                    input_field.without_auto_validation()

                    with input_field.add_slot('append'):
                        edit_btn = ui.button(icon='edit').props(
                            'round dense flat')
                        save_btn = ui.button(icon='save').props(
                            'round dense flat')
                        save_btn.set_visibility(False)

                    input_field.on('blur', lambda: (
                        edit_btn.set_visibility(True),
                        save_btn.set_visibility(False),
                        input_field.props(add='readonly'),
                    ))

                    edit_btn.on_click(lambda: (
                        input_field.props(remove='readonly'),
                        edit_btn.set_visibility(False),
                        save_btn.set_visibility(True),
                        input_field.run_method('focus'),
                    ))

                return input_field, save_btn

            fn, fn_save = await editable_field('First Name', person.first_name, validation=name_validation)
            fn_save.on_click(lambda: modify_fn(fn))

            ln, ln_save = await editable_field('Last Name', person.last_name, validation=name_validation)
            ln_save.on_click(lambda: modify_ln(ln))

            email, email_save = await editable_field('Email', person.email, validation=email_validation)
            email_save.on_click(lambda: modify_email(email))

            instagram, instagram_save = await editable_field('Instagram Handle', person.instagram_handle, validation=insta_validation)
            instagram_save.on_click(lambda: modify_instagram(instagram))

        with section():
            secondary_button('Logout', on_click=lambda: ui.navigate.to('/logout'))
