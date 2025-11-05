from google.oauth2 import id_token
from fastapi import Depends, HTTPException, Request
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as google_req
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


async def validate_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        id_token.verify_token(credentials.credentials, google_req())
    except GoogleAuthError:
        raise HTTPException(401, "Invalid token")
