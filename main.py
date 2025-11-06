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
from services.auth import verify_admin_token
from services.drive import drive_service


class NoWebSocketFilter(logging.Filter):
    def filter(self, record):
        return "WebSocket" not in record.getMessage()


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").addFilter(NoWebSocketFilter())
    await drive_service.__aenter__()
    yield
    await drive_service.__aexit__(None, None, None)

app = FastAPI(lifespan=lifespan)

env = os.getenv('env')
bearer_auth = [Depends(verify_admin_token)]

app.include_router(member_router, dependencies=bearer_auth)
app.include_router(ticket_router, dependencies=bearer_auth)
app.include_router(payment_router, dependencies=bearer_auth)
app.include_router(person_router)
app.include_router(event_router)
app.include_router(venue_router)
app.include_router(user_router)

app.include_router(auth_router)
app.include_router(tg_router)
app.include_router(attendance_router)
app.include_router(apple_pass_updates)

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
    from nicegui import ui

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
        app,
        favicon=favicon_path,
        title="Drop Dead Disco",
        reconnect_timeout=30.0,
        dark=False,
        storage_secret=storage_secret
    )


main()
