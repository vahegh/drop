from contextlib import asynccontextmanager
from nicegui import ui, app
from consts import (DROP_INSTA_URL, DROP_SPOTIFY_URL,
                    support_email, DROP_YOUTUBE_URL, logo_gray_path)
from components import primary_button, section_title, section, login_button
from api_models import PersonResponseFull
from helpers import gtag_config, is_cloud_run


@asynccontextmanager
async def frame(show_footer=False):
    ui.colors(primary="#f3f4f6", dark="#2a2e38", secondary="#ff50ad", light="#f3f4f6",
              accent="#8e51ff", positive="#50bf5a", warning="#ff8904", negative="#fb2c36")

    request = ui.context.client.request

    person: PersonResponseFull = request.state.person
    logged_in = request.state.logged_in

    gtag_params = {}
    if not is_cloud_run():
        gtag_params['debug_mode'] = True
    if logged_in:
        gtag_params['user_id'] = str(person.id)

    gtag_config(gtag_params)

    show_signin = request.url.path not in ['/signup', '/login']
    login_redirect_url = request.url.path if show_signin else '/'
    # await ui.context.client.connected()
    menu = ui.right_drawer(value=False).props(':press-delay="0"').classes('items-center')

    with ui.context.client.content.classes('gap-4 px-0 py-18 pb-4 w-full items-center justify-center') as content:
        with ui.row().classes('fixed top-0 left-0 items-center bg-transparent h-14 px-4 py-2 backdrop-blur-xs flex justify-between z-10'):
            with ui.button().props('flat href="/"').classes('py-0 px-2'):
                ui.image(logo_gray_path).classes(
                    'w-14 h-8')
            ui.space()

            if logged_in:
                with ui.button().props('round flat').classes('p-0') as btn:
                    if person.avatar_url:
                        ui.image(person.avatar_url).classes('w-[32px] rounded-full')
                    else:
                        ui.icon('account_circle', size='32px', color="gray")

                    with menu:
                        with section() as sec:
                            sec.classes('text-center')

                            if person.avatar_url:
                                ui.image(person.avatar_url).classes(
                                    'w-[80px] rounded-full')
                            else:
                                ui.icon('account_circle', size='80px')

                            section_title(person.full_name)

                            ui.link(f"@{person.instagram_handle}",
                                    f"https://instagram.com/{person.instagram_handle}").classes('no-underline')

                        primary_button('Your profile', target='/profile')

                        options = {
                            None: "Auto",
                            True: "Dark",
                            False: "Light"
                        }
                        ui.toggle(options).props(
                            'toggle-color=accent').bind_value(ui.dark_mode(None))

                        ui.link('Log out', '/logout')

                    btn.on_click(menu.toggle)

            else:
                if show_signin:
                    login_button(target=f'/login?redirect_url={login_redirect_url}')

        yield content

    if show_footer:
        with ui.column().classes('border-t-1 border-gray-300 dark:border-gray-700 h-auto z-0 w-full gap-1'):
            with ui.column().classes('gap-1 w-full items-center'):
                with ui.link(target='/'):
                    ui.image(logo_gray_path).classes('w-20 h-10').props('no-spinner')
                ui.link("Home", '/')
                ui.link("About us", '/about')
                ui.link("Policy", '/policy')

            with ui.row().classes('justify-center gap-0'):
                ui.button(icon="img:/static/images/instagram.svg",
                          color=None).props(f'flat href={DROP_INSTA_URL}').classes('dark:invert')
                ui.button(icon="img:/static/images/spotify.svg",
                          color=None).props(f'flat href={DROP_SPOTIFY_URL}').classes('dark:invert')
                ui.button(icon="img:/static/images/youtube.svg",
                          color=None).props(f'flat href={DROP_YOUTUBE_URL}').classes('dark:invert')

            with ui.column().classes('gap-1 w-full items-center'):
                ui.link(support_email,
                        target=f"mailto:{support_email}").classes('text-xs')
