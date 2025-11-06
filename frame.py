from contextlib import asynccontextmanager
from nicegui import ui, app
from consts import (spotify_logo_path, instagram_logo_path,
                    DROP_INSTA_URL, DROP_SPOTIFY_URL, support_email, logo_white_path,
                    DROP_YOUTUBE_URL, youtube_logo_path, APP_BASE_URL, google_client_id, logo_gray_path)
from elements import google_button, secondary_button
from helpers import set_user_data


@asynccontextmanager
async def frame(show_footer=True, show_signin=True):
    ui.colors(primary="#FFFFFF", dark="#101010", secondary="#df296f",
              accent="#9D20C3", section="#61007F")

    st = app.storage.user

    with ui.header(bordered=True).classes('items-center bg-transparent h-14 px-6 py-2 backdrop-blur-xs flex justify-between'):
        ui.image(logo_gray_path).classes(
            'w-16 h-10 object-contain').on('click', lambda: ui.navigate.to('/'))
        ui.space()
        logged_in = await set_user_data(ui.context.client.request)

        if logged_in:
            avatar_url = st.get('avatar_url')
            with ui.button().props('round flat outline') as btn:
                avatar = ui.image(avatar_url).classes(
                    'size-8 rounded-full')
                btn.classes.clear()
                with ui.menu().classes('items-center justify-center p-2') as menu:
                    with ui.column().classes('items-center'):
                        ui.image(avatar_url).classes(
                            'size-20 rounded-full')
                        ui.label(st['name']).classes('text-center')
                        b = secondary_button('Logout')
                        b.on_click(lambda: b.props(add='loading'))
                        b.on_click(lambda: ui.navigate.to(
                            f'/logout?redirect_url={ui.context.client.request.url}'))

                avatar.on('click', menu.open)

        else:
            if show_signin:
                ui.html(f'''
                <div id="g_id_onload"
                    data-client_id="{google_client_id}"
                    data-context="signin"
                    data-ux_mode="redirect"
                    data-login_uri="{APP_BASE_URL}/api/auth/login"
                    data-auto_select="false"
                    data-itp_support="true"
                    data-use_fedcm_for_prompt="true"
                    data-use_fedcm_for_button="true">
                </div>''', sanitize=False)

                google_button(ui.context.client.request.url.path)

    with ui.context.client.content.classes('h-full p-0 gap-0 w-full items-center justify-between') as content:
        with ui.grid().classes('flex w-full items-center justify-center p-4 gap-8') as content:
            yield content, logged_in

    if show_footer:
        with ui.footer(fixed=False, bordered=True).classes('bg-dark h-auto z-0'):
            with ui.column().classes('gap-1 w-full items-center'):
                ui.image(logo_white_path).props(
                    'no-spinner').classes('w-20 h-10').on('click', lambda: ui.navigate.to('/'))
                ui.link("Home", '/').classes('text-white')
                ui.link("About us", '/about').classes('text-white')
                ui.link("Policy", '/policy').classes('text-white')

            with ui.row().classes('justify-center'):
                ui.image(instagram_logo_path).classes('w-8').on('click',
                                                                lambda: ui.navigate.to(DROP_INSTA_URL))
                ui.image(spotify_logo_path).classes('w-8').on('click',
                                                              lambda: ui.navigate.to(DROP_SPOTIFY_URL))
                ui.image(youtube_logo_path).classes('w-8').on('click',
                                                              lambda: ui.navigate.to(DROP_YOUTUBE_URL))

            with ui.column().classes('gap-1 w-full items-center'):
                ui.link(support_email,
                        target=f"mailto:{support_email}").classes('text-xs')
                ui.label("123 Andranik Str, Yerevan, Armenia 0004").classes(
                    'text-xs text-gray-600')
