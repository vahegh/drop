import os
from dotenv import load_dotenv

if os.path.exists('.env'):
    load_dotenv()


import logging
from helpers import is_cloud_run

from contextlib import asynccontextmanager
from fastapi import FastAPI

from routes.auth import router as auth_router
from routes.telegram_webhook import router as tg_webhook_router
from routes.attendance import router as attendance_router
from routes.apple_pass_updates import router as apple_pass_updates

from dependencies import AuthMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NoWebSocketFilter(logging.Filter):
    def filter(self, record):
        return "WebSocket" not in record.getMessage()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").addFilter(NoWebSocketFilter())
    yield

fastapi_app = FastAPI(lifespan=lifespan)

env = os.getenv('env')


fastapi_app.include_router(auth_router)
fastapi_app.include_router(tg_webhook_router)
fastapi_app.include_router(attendance_router)
fastapi_app.include_router(apple_pass_updates)

storage_secret = os.getenv('storage_secret')

head_html = '''
<meta name="description" content="Drop Dead Disco - it's like a cult, but you can keep your job.">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />

<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Icons" rel="stylesheet">

<style>
    .nicegui-markdown p {
        margin: 0;
    }

    body.body--light {
        background-color: #f3f4f6;
    }
    body.body--dark {
        background-color: #24262b;
    }

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

    .q-radio__label {
        width: 100%;
    }

    .q-radio {
        width: 100%;
        align-items: start;
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

    import components

    from pages import (about,
                       admin,
                       event,
                       home,
                       unsubscribe,
                       buy_ticket,
                       callback,
                       policy,
                       signup,
                       login,
                       logout,
                       profile,
                       errors)

    ui.run_with(
        fastapi_app,
        favicon="static/images/favicon.png",
        title="Drop Dead Disco",
        reconnect_timeout=30.0,
        dark=None,
        storage_secret=storage_secret,
    )
    app.add_middleware(AuthMiddleware)


main()
