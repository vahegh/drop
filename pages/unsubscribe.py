from nicegui import app
from fastapi import Request, status
from fastapi.responses import JSONResponse


@app.post('/unsubscribe')
async def unsubscribe_page(request: Request):
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
