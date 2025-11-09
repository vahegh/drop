from fastapi import Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from services.user import user_info
from routes.auth import refresh, logout


def logged_in(request: Request) -> bool:
    return getattr(request.state, "logged_in", False)


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
                    return await logout(refresh_token)
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
