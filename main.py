import os
from dotenv import load_dotenv

if os.path.exists('.env'):
    load_dotenv()


from helpers import is_cloud_run
from routes.auth import router as auth_router
from routes.telegram_webhook import router as tg_webhook_router
from routes.attendance import router as attendance_router
from routes.apple_pass_updates import router as apple_pass_updates
from routes.event import router as event_router
from dependencies import AuthMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)


env = os.getenv('env')
storage_secret = os.getenv('storage_secret')

head_html = '''
<meta name="description" content="Drop Dead Disco - it's like a cult, but you can keep your job.">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Icons" rel="stylesheet">

<script src="https://www.googletagmanager.com/gtag/js?id=G-152G4X4VLJ" async defer></script>

<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
</script>

<style>

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

pixel_code = '''
<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '2205711949883411');
fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id=2205711949883411&ev=PageView&noscript=1"
/></noscript>
<!-- End Meta Pixel Code -->
'''


def main():
    from nicegui import ui, app

    ui.add_head_html(head_html, shared=True)
    if env != "local":
        ui.add_head_html(pixel_code, shared=True)

    import components
    from pages import (
        about,
        admin,
        event,
        errors,
        home,
        unsubscribe,
        buy_ticket,
        callback,
        policy,
        signup,
        login,
        logout,
        profile,
    )

    app.include_router(auth_router)
    app.include_router(tg_webhook_router)
    app.include_router(attendance_router)
    app.include_router(apple_pass_updates)
    app.include_router(event_router)
    app.add_middleware(AuthMiddleware)
    app.add_static_files(url_path='/static',
                         local_directory=os.path.join(os.path.dirname(__file__), 'static'))
    ui.run(
        favicon="static/images/favicon.png",
        title="Drop Dead Disco",
        viewport="width=device-width, initial-scale=1, maximum-scale=1",
        reconnect_timeout=30.0,
        dark=None,
        storage_secret=storage_secret,
        reload=False,
        show=False,
        fastapi_docs=True
    )


if __name__ == "__main__":
    main()
