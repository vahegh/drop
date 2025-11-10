from contextlib import asynccontextmanager
from nicegui import ui
from consts import (spotify_logo_path, instagram_logo_path,
                    DROP_INSTA_URL, DROP_SPOTIFY_URL, support_email, logo_white_path,
                    DROP_YOUTUBE_URL, youtube_logo_path, APP_BASE_URL, google_client_id, logo_gray_path)
from elements import google_button, secondary_button, section_title, primary_button
from api_models import PersonResponseFull


@asynccontextmanager
async def frame(show_footer=True):
    ui.colors(primary="#FFFFFF", dark="#101010", secondary="#df296f",
              accent="#9D20C3", section="#61007F")

    request = ui.context.client.request

    person: PersonResponseFull = request.state.person
    logged_in = request.state.logged_in
    show_signin = request.url not in ['/signup']
    await ui.context.client.connected()

    with ui.row().classes('fixed top-0 left-0 items-center bg-transparent h-14 px-4 py-2 backdrop-blur-xs flex justify-between z-10'):
        with ui.button().props('flat').classes('py-0 px-2').on('click', lambda: ui.navigate.to('/')):
            ui.image(logo_gray_path).classes(
                'w-14 h-8')
        ui.space()

        if logged_in:
            with ui.button().props('round flat').classes('p-0') as btn:
                if person.avatar_url:
                    ui.image(person.avatar_url).classes('w-8 rounded-full')
                else:
                    ui.icon('account_circle', size='lg')

                with ui.menu().props() as menu:
                    with ui.column().classes('items-center w-full p-4'):
                        if person.avatar_url:
                            ui.image(person.avatar_url).classes(
                                'size-20 rounded-full')
                        else:
                            ui.icon('account_circle', size='xl')

                        section_title(person.full_name).classes('text-center')
                        profile_btn = primary_button('Your profile').on_click(
                            lambda: (
                                ui.navigate.to('/profile'),
                                profile_btn.props(add='loading disable')
                            ))
                        logout_btn = secondary_button('Logout').on_click(lambda: (
                            ui.navigate.to(f'/logout?redirect_url={request.url}'),
                            logout_btn.props(add='loading disable')
                        ))
                btn.on_click(menu.toggle)

        else:
            if show_signin:
                ui.run_javascript(f'''
                    google.accounts.id.initialize({{
                        client_id: '759529195467-d4dt9f5do5iu4g4itndu2v0q9vpmip93.apps.googleusercontent.com',
                        ux_mode: 'redirect',
                        login_uri: '{APP_BASE_URL}/api/auth/login',
                        auto_select: false,
                        itp_support: true,
                        use_fedcm_for_prompt: true,
                        use_fedcm_for_button: true
                    }});''')

                # google_button(request.url.path)

                ui.button("Log in").classes(
                    'rounded-full bg-primary text-accent', remove='text-black').props('size="12px" outline no-caps').on_click(lambda: ui.navigate.to(f'/login?redirect_url={request.url}'))

    with ui.context.client.content.classes('bg-gray-100 p-0 gap-0 w-full items-center justify-center min-h-[100vh]') as content:
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
