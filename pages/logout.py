from nicegui import app, ui
from routes.auth import logout


@ui.page('/logout', title="Log Out | Drop Dead Disco", response_timeout=10)
async def logout_page(redirect_url='/'):
    app.storage.user.clear()
    return await logout(ui.context.client.request.cookies.get('refresh_token'), redirect_url)
