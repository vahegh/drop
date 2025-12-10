from nicegui import ui, app
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from frame import frame
from components import section, primary_button, destructive_button
from services.person import get_person_by_email


@app.post('/unsubscribe')
async def unsubscribe(request: Request):
    form_data = await request.form()
    email = form_data.get('email')

    if not email:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Email is required"}
        )

    print(f"Unsubscribe request received for: {email}")

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{email} unsubscribed successfully"}
    )


@ui.page('/unsubscribe', title="Unsubscribe | Drop Dead Disco")
async def unsubscribe_page(email):
    if not email:
        raise HTTPException(400, "Email is required.")

    person = await get_person_by_email(email)
    if not person:
        raise HTTPException(404, "No such person")

    async with frame() as f:
        f.classes('min-h-[100svh] px-4')

        async def unsubscribe():
            print(f"Unsubscribe request received for {email}")
            c.clear()
            with c:
                with section("You have unsubscribed from Drop Dead Disco.", subtitle="We're sad to see you go."):
                    pass

        async def delete_account():
            del_btn.props(add='loading')
            if await ui.run_javascript(
                    'confirm("Are you sure you want to delete your account?")', timeout=10):
                print(f"Delete account request received for {email}")
                c.clear()
                with c:
                    with section("Your account will be deleted shortly."):
                        pass
            del_btn.props(remove='loading')

        with ui.card() as c:
            with section(
                "Unsubscribe?",
                subtitle=f"It may take a few days for you to stop receiving email from us at {email}"
            ):
                unsub_btn = primary_button("Unsubscribe").on_click(lambda: unsubscribe())
                del_btn = destructive_button(
                    "Delete my account instead").on_click(lambda: delete_account())
