from nicegui import ui, app
from nicegui.events import UploadEventArguments
from consts import APP_BASE_URL, name_validation, email_validation, insta_validation
from elements import (primary_button, secondary_button, status_icon,
                      page_header, section, toast, instagram_dialog,
                      destructive_button, positive_button)
from services.person import update_person, get_person_by_email
from services.cloud_storage import upload_avatar
from api_models import PersonResponseFull, PersonUpdate
from frame import frame
from dependencies import logged_in, Depends
from fastapi import Request
from services.instagram_check import instagram_check
import random
from services.mailing import EmailRequest, send_email
from services.templating import generate_template
import io
from PIL import Image
import base64


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

        async def modify_email(new_email):
            async def send_otp(new_email):
                send_btn.props(add='loading disable')
                otp = random.randint(100000, 999999)
                app.storage.user['otp'] = str(otp)
                context = {"name": person.first_name, "otp": otp}
                template = await generate_template("otp.html", context=context)
                outgoing_email = EmailRequest(
                    recipient_email=new_email,
                    subject="Your OTP",
                    body=template
                )
                await send_email(outgoing_email)
                send_btn.props(remove='loading disable')
                send_btn.set_text("Send again")
                save_btn.set_visibility(True)
                otp_input.set_visibility(True)

            if not new_email.validate():
                return

            async def verify_otp(otp):
                save_btn.props(add='loading disable')
                result = otp == app.storage.user['otp']
                if result:
                    try:
                        await update_person(person.id, PersonUpdate(email=email.value))
                    except Exception as e:
                        toast(f"Unable to save email: {str(e)}")
                    else:
                        toast(f"Updated email to {email.value}.")
                        dl.delete()
                    finally:
                        app.storage.user.clear()

                else:
                    toast(f"Incorrect OTP")

                save_btn.props(remove='loading disable')

            existing_user = await get_person_by_email(new_email.value)
            if existing_user:
                toast("This email is already used.", type='warning')
                return

            with ui.dialog(value=True) as dl:
                with ui.card().classes('w-full'):
                    with section("Verify email", subtitle="Send a one-time code to your new email to verify."):
                        ui.label(new_email.value)

                        otp_input = ui.input("OTP")
                        otp_input.set_visibility(False)

                        save_btn = secondary_button("Verify").on_click(
                            lambda: verify_otp(otp_input.value))
                        save_btn.set_visibility(False)

                        send_btn = primary_button("Send OTP").on_click(
                            lambda: send_otp(new_email.value))

        async def handle_upload(e: UploadEventArguments):
            file_bytes = e.file._data
            img = Image.open(io.BytesIO(file_bytes))

            size = min(img.width, img.height)
            left = (img.width - size) // 2
            top = (img.height - size) // 2
            img = img.crop((left, top, left + size, top + size))

            img = img.resize((256, 256), Image.Resampling.LANCZOS)

            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            optimized_bytes = io.BytesIO()
            img.save(optimized_bytes, format='JPEG', quality=85, optimize=True)
            optimized_bytes = optimized_bytes.getvalue()

            base64_string = base64.b64encode(optimized_bytes).decode('utf-8')
            image_src = f"data:image/jpeg;base64,{base64_string}"

            with ui.dialog(value=True) as dl:
                with ui.card().classes('w-80'):
                    ui.image(image_src).classes('size-48 rounded-full')
                    with ui.row(wrap=False):
                        primary_button("Cancel").on_click(lambda: dl.submit(False))
                        save_btn = positive_button("Save").on_click(lambda: dl.submit(True))

            result = await dl

            if result:
                save_btn.props(add='loading disable')
                filename = person.id
                avatar_url = await upload_avatar(
                    filename,
                    file_bytes=optimized_bytes,
                    content_type='image/jpeg'
                )
                await update_person(person.id, PersonUpdate(avatar_url=avatar_url))
                ui.notify(f'Avatar updated')
                ui.navigate.to('/profile')

            dl.delete()

        with section():
            with ui.element('div').classes('relative inline-block'):
                if person.avatar_url:
                    ui.image(person.avatar_url).classes('size-20 rounded-full')
                else:
                    ui.icon('account_circle', size='80px')

                upload = ui.upload(
                    max_files=1,
                    max_file_size=1000000,
                    auto_upload=True,
                    on_upload=lambda e: handle_upload(e),
                    on_rejected=lambda: toast(
                        "Please select a different picture. JPEG and PNG files under 1MB are supported.", timeout=3, type='warning')
                ).props('flat accept="image/jpeg, image/png" no-thumbnails').classes('hidden')

                avatar_edit_btn = ui.button(color="secondary").props('unelevated round size="8px"').classes(
                    'absolute bottom-0 right-0').on_click(lambda: upload.run_method('pickFiles'))
                with avatar_edit_btn:
                    ui.icon('edit', size='16px')

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
                            'round dense flat color="dark"')
                        save_btn = ui.button(icon='save').props(
                            'round dense flat color="dark"')
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
            destructive_button('Logout', on_click=lambda: ui.navigate.to('/logout'))
