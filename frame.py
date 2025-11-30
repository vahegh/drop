from contextlib import asynccontextmanager
from nicegui import ui, app
from consts import (DROP_INSTA_URL, DROP_SPOTIFY_URL,
                    support_email, DROP_YOUTUBE_URL, logo_gray_path)
from elements import primary_button, destructive_button, section, login_button
from api_models import PersonResponseFull


@asynccontextmanager
async def frame(show_footer=False):
    ui.colors(primary="#f3f4f6", dark="#2a2e38", secondary="#f6339a", light="#f3f4f6",
              accent="#8e51ff", positive="#50bf5a", warning="#ff8904", negative="#fb2c36")

    request = ui.context.client.request

    person: PersonResponseFull = request.state.person
    logged_in = request.state.logged_in
    show_signin = True
    login_redirect_url = request.url.path if request.url.path not in ['/signup', '/login'] else '/'
    await ui.context.client.connected()
    menu = ui.right_drawer(value=False).props(':press-delay="0"')

    with ui.context.client.content.classes('gap-4 px-0 py-18 pb-4 w-full items-center justify-center') as content:
        with ui.row().classes('fixed top-0 left-0 items-center bg-transparent h-14 px-4 py-2 backdrop-blur-xs flex justify-between z-10'):
            with ui.button().props('flat').classes('py-0 px-2').on('click', lambda: ui.navigate.to('/')):
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
                        with section():
                            if person.avatar_url:
                                ui.image(person.avatar_url).classes(
                                    'w-[80px] rounded-full')
                            else:
                                ui.icon('account_circle', size='80px')

                        with section(person.full_name) as sec:
                            ui.link(f"@{person.instagram_handle}",
                                    f"https://instagram.com/{person.instagram_handle}").classes('no-underline')
                            sec.classes('text-center')

                        with section():
                            profile_btn = primary_button('Your profile').on_click(
                                lambda: (
                                    ui.navigate.to('/profile'),
                                    profile_btn.props(add='loading disable')
                                ))
                            ui.link('Log out', '/logout')
                    btn.on_click(menu.toggle)

            else:
                if show_signin:
                    login_button().on_click(lambda: ui.navigate.to(
                        f'/login?redirect_url={login_redirect_url}'))

        yield content

    if show_footer:
        with ui.column().classes('border-t-1 border-gray-300 dark:border-gray-700 h-auto z-0 w-full gap-1'):
            with ui.column().classes('gap-1 w-full items-center'):
                ui.image(logo_gray_path).props(
                    'no-spinner').classes('w-20 h-10').on('click', lambda: ui.navigate.to('/'))
                ui.link("Home", '/')
                ui.link("About us", '/about')
                ui.link("Policy", '/policy')

            with ui.row().classes('justify-center gap-0'):
                app.add_static_files(url_path='/static/images', local_directory='static/images')
                ui.button(icon="img:/static/images/instagram.svg",
                          color=None).props('flat').classes('dark:invert').on_click(lambda: ui.navigate.to(DROP_INSTA_URL))
                ui.button(icon="img:/static/images/spotify.svg",
                          color=None).props('flat').classes('dark:invert').on_click(lambda: ui.navigate.to(DROP_SPOTIFY_URL))
                ui.button(icon="img:/static/images/youtube.svg",
                          color=None).props('flat').classes('dark:invert').on_click(lambda: ui.navigate.to(DROP_YOUTUBE_URL))

            with ui.column().classes('gap-1 w-full items-center'):
                ui.link(support_email,
                        target=f"mailto:{support_email}").classes('text-xs')
