from nicegui import ui, Client, app
from nicegui.page import page
from fastapi import Request, Response
from components import secondary_button, page_header, section_title
from frame import frame


@app.exception_handler(404)
async def exception_handler_404(request: Request, exception: Exception) -> Response:
    with Client(page('', title='404 Not Found'), request=request) as client:
        async with frame():
            with ui.column():
                page_header('404 - Not Found')
            ui.image('static/images/404.gif')
            with ui.column().classes('p-4'):
                ui.label('Lost?').classes('text-lg')
                secondary_button("Go home").on_click(lambda: ui.navigate.to('/'))
        return ui.context.client.build_response(request, 404)


@app.exception_handler(401)
async def exception_handler_401(request: Request, exception: Exception) -> Response:
    with Client(page('', title='401 Unauthorized'), request=request) as client:
        async with frame():
            with ui.column():
                page_header('401 - Unauthorized')
            ui.image('static/images/401.webp')
            with ui.column().classes('p-4'):
                ui.label('You can always go back home').classes('text-lg')
                secondary_button("Go home").on_click(lambda: ui.navigate.to('/'))
        return ui.context.client.build_response(request, 401)
