from contextlib import asynccontextmanager
from nicegui import ui
from consts import (spotify_logo_path, instagram_logo_path,
                    DROP_INSTA_URL, DROP_SPOTIFY_URL, support_email, logo_white_path,
                    DROP_YOUTUBE_URL, youtube_logo_path, logo_gray_path)
from elements import section_title, primary_button, destructive_button
from api_models import PersonResponseFull


@asynccontextmanager
async def frame(show_footer=True):
    ui.colors(primary="#FFFFFF", dark="#101010", secondary="#df296f",
              accent="#9D20C3", section="#61007F", negative="#D50E0E")

    request = ui.context.client.request

    person: PersonResponseFull = request.state.person
    logged_in = request.state.logged_in
    show_signin = True
    login_redirect_url = request.url.path if request.url.path not in ['/signup', '/login'] else '/'
    await ui.context.client.connected()

    with ui.context.client.content.classes('bg-gray-100 gap-4 px-0 py-14 w-full items-center justify-center min-h-[100svh]') as content:
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

                    menu = ui.menu().classes('w-48 bg-gray-100')

                    with menu:
                        with ui.column().classes('items-center w-full p-4'):
                            if person.avatar_url:
                                ui.image(person.avatar_url).classes(
                                    'w-[80px] rounded-full')
                            else:
                                ui.icon('account_circle', size='80px')

                            section_title(person.full_name).classes('text-center')
                            profile_btn = primary_button('Your profile').on_click(
                                lambda: (
                                    ui.navigate.to('/profile'),
                                    profile_btn.props(add='loading disable')
                                ))
                            logout_btn = destructive_button('Logout').on_click(lambda: (
                                ui.navigate.to(f'/logout?redirect_url={login_redirect_url}'),
                                logout_btn.props(add='loading disable')
                            ))
                    btn.on_click(menu.toggle)

            else:
                if show_signin:
                    ui.button("Log in").classes(
                        'rounded-full bg-primary text-black').props('size="12px" outline no-caps').on_click(lambda: ui.navigate.to(f'/login?redirect_url={login_redirect_url}'))

        yield content

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
