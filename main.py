from fastapi import Request
from consts import favicon_path
from helpers import is_cloud_run
import logging
import os

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from routes.auth import router as auth_router
from routes.venue import router as venue_router
from routes.event import router as event_router
from routes.telegram import router as tg_router
from routes.person import router as person_router
from routes.user import router as user_router
from routes.payment import router as payment_router
from routes.member_pass import router as member_router
from routes.event_ticket import router as ticket_router
from routes.attendance import router as attendance_router
from routes.apple_pass_updates import router as apple_pass_updates
from starlette.middleware.base import BaseHTTPMiddleware
from services.drive import drive_service
from fastapi import Request, HTTPException
from routes.auth import refresh, logout
from routes.user import user_info, modify_user
from api_models import PersonUpdate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NoWebSocketFilter(logging.Filter):
    def filter(self, record):
        return "WebSocket" not in record.getMessage()


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        access_token = request.cookies.get('access_token')
        refresh_token = request.cookies.get('refresh_token')

        request.state.logged_in = False
        request.state.person = None

        if request.url.path.startswith('/api'):
            return await call_next(request)

        if request.url.path in ['/logout', '/login', '/signup']:
            return await call_next(request)

        async def silent_refresh():
            if refresh_token:
                try:
                    return await refresh(request)
                except HTTPException:
                    return await logout()
            else:
                return await call_next(request)

        if access_token:
            try:
                person = await user_info(request)
            except HTTPException:
                return await silent_refresh()

        else:
            return await silent_refresh()

        request.state.logged_in = True
        request.state.person = person

        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").addFilter(NoWebSocketFilter())
    await drive_service.__aenter__()
    yield
    await drive_service.__aexit__(None, None, None)

fastapi_app = FastAPI(lifespan=lifespan)

env = os.getenv('env')

fastapi_app.include_router(member_router)
fastapi_app.include_router(ticket_router)
fastapi_app.include_router(payment_router)
fastapi_app.include_router(person_router)
fastapi_app.include_router(event_router)
fastapi_app.include_router(venue_router)
fastapi_app.include_router(user_router)

fastapi_app.include_router(auth_router)
fastapi_app.include_router(tg_router)
fastapi_app.include_router(attendance_router)
fastapi_app.include_router(apple_pass_updates)

storage_secret = os.getenv('storage_secret')

head_html = '''
<meta name="description" content="Drop Dead Disco - it's like a cult, but you can keep your job.">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />

<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@100;200;300;400;500;600;700;900&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Icons" rel="stylesheet">

<meta name="google-signin-client_id" content="759529195467-d4dt9f5do5iu4g4itndu2v0q9vpmip93.apps.googleusercontent.com">
<script src="https://accounts.google.com/gsi/client?hl=en"></script>

<style>
    * { font-family: 'Montserrat' }

    html {
        scroll-behavior: smooth;
    }

    @keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.03); }
    100% { transform: scale(1); }
    }

    .pulse-animation {
    animation: pulse 0.5s ease-in-out;
    }

    .event-card-img {
        object-fit: cover;
        border-radius: 16px;
        width: 100%;
        height: 100%;
        min-height: 420px;
    }

    .q-btn--push.q-btn--actionable {
        transition: transform 0.05s cubic-bezier(0.25,0.8,0.5,1);
    }
</style>
'''

if not is_cloud_run():
    gtag_html = '''
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-152G4X4VLJ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-152G4X4VLJ', { 'debug_mode':true });
</script>
'''
else:
    gtag_html = '''
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-152G4X4VLJ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-152G4X4VLJ');
</script>
'''


def main():
    from nicegui import ui, app

    ui.add_head_html(head_html, shared=True)
    ui.add_head_html(gtag_html, shared=True)

    import elements

    from pages import (about,
                       admin,
                       event,
                       home,
                       unsubscribe,
                       buy_ticket,
                       callback,
                       policy,
                       signup,
                       logout,
                       errors)

    ui.run_with(
        fastapi_app,
        favicon=favicon_path,
        title="Drop Dead Disco",
        reconnect_timeout=30.0,
        dark=False,
        storage_secret=storage_secret
    )
    app.add_middleware(AuthMiddleware)


main()
