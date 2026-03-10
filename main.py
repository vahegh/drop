import os
from dotenv import load_dotenv

if os.path.exists('.env'):
    load_dotenv()


from routes.auth import router as auth_router
from routes.callbacks import router as callbacks_router
from routes.telegram_webhook import router as tg_webhook_router
from routes.attendance import router as attendance_router
from routes.apple_pass_updates import router as apple_pass_updates
from routes.event import router as event_router
from routes.client import auth as client_auth
from routes.client import events as client_events
from routes.client import venues as client_venues
from routes.client import people as client_people
from routes.client import drinks as client_drinks
from routes.client import payments as client_payments
from routes.client import tickets as client_tickets
from routes.admin import auth as admin_auth
from routes.admin import people as admin_people
from routes.admin import events as admin_events
from routes.admin import payments as admin_payments
from routes.admin import venues as admin_venues
from routes.admin import drinks as admin_drinks
from routes.admin import tickets as admin_tickets
from routes.admin import tiers as admin_tiers
from fastapi import Depends
from decorators import verify_admin_token
from dependencies import AuthMiddleware
import logging

logger = logging.getLogger(__name__)

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)


env = os.getenv('env')


def main():
    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn

    app = FastAPI(title="Drop Dead Disco", docs_url="/docs")

    app.include_router(auth_router)
    app.include_router(callbacks_router)
    app.include_router(tg_webhook_router)
    app.include_router(attendance_router)
    app.include_router(apple_pass_updates)
    app.include_router(event_router)
    app.include_router(client_auth.router, prefix="/api/client")
    app.include_router(client_events.router, prefix="/api/client")
    app.include_router(client_venues.router, prefix="/api/client")
    app.include_router(client_people.router, prefix="/api/client")
    app.include_router(client_drinks.router, prefix="/api/client")
    app.include_router(client_payments.router, prefix="/api/client")
    app.include_router(client_tickets.router, prefix="/api/client")
    app.include_router(admin_auth.router, prefix="/api/admin")
    app.include_router(admin_people.router, prefix="/api/admin", dependencies=[Depends(verify_admin_token)])
    app.include_router(admin_events.router, prefix="/api/admin", dependencies=[Depends(verify_admin_token)])
    app.include_router(admin_payments.router, prefix="/api/admin", dependencies=[Depends(verify_admin_token)])
    app.include_router(admin_venues.router, prefix="/api/admin", dependencies=[Depends(verify_admin_token)])
    app.include_router(admin_drinks.router, prefix="/api/admin", dependencies=[Depends(verify_admin_token)])
    app.include_router(admin_tickets.router, prefix="/api/admin", dependencies=[Depends(verify_admin_token)])
    app.include_router(admin_tiers.router, prefix="/api/admin", dependencies=[Depends(verify_admin_token)])

    if env == "local":
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(AuthMiddleware)

    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    app.mount('/static', StaticFiles(directory=static_dir), name='static')

    # Serve React frontend (built)
    frontend_dist = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')
    if os.path.isdir(frontend_dist):
        app.mount('/assets', StaticFiles(directory=os.path.join(frontend_dist, 'assets')), name='assets')

        index_path = os.path.join(frontend_dist, 'index.html')
        with open(index_path, 'r', encoding='utf-8') as f:
            index_html = f.read()
        env_script = f'<script>window.__ENV__ = "{env or "production"}";</script>'
        index_html = index_html.replace('<head>', f'<head>\n    {env_script}', 1)

        from fastapi.responses import HTMLResponse

        @app.get('/{full_path:path}', include_in_schema=False)
        async def serve_react(full_path: str):
            return HTMLResponse(index_html)

    uvicorn.run(app, host='0.0.0.0', port=8080)


if __name__ == "__main__":
    main()
