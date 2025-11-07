from fastapi import Request, Depends


def logged_in(request: Request) -> bool:
    return getattr(request.state, "logged_in", False)
