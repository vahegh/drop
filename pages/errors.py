from nicegui import ui, Client, app
from nicegui.page import page
from fastapi import Request, Response
from components import primary_button, page_header, section
from frame import frame


@app.exception_handler(404)
async def exception_handler_404(request: Request, exception: Exception) -> Response:
    with Client(page('', title='404 Not Found'), request=request) as client:
        async with frame():
            with section():
                page_header('404 - Not Found')
            with section():
                ui.image('static/images/404.gif')
            with section("Lost?"):
                primary_button("Go home", target='/')
        return ui.context.client.build_response(request, 404)


@app.exception_handler(401)
async def exception_handler_401(request: Request, exception: Exception) -> Response:
    with Client(page('', title='401 Unauthorized'), request=request) as client:
        async with frame():
            with section():
                page_header('401 - Unauthorized')
            with section():
                ui.image('static/images/401.webp')
            with section("You can always go back home"):
                primary_button("Go home", target='/')
        return ui.context.client.build_response(request, 401)
