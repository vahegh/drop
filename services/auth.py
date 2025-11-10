import os
import jwt
from uuid import uuid4
from datetime import timezone, datetime, timedelta

TOKEN_EXPIRATION_MINUTES = 15
auth_secret = os.environ['auth_secret']


async def create_jwt(email, expires_in: int = TOKEN_EXPIRATION_MINUTES):
    token = jwt.encode({
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in),
        "iat": datetime.now(timezone.utc).timestamp()
    }, auth_secret, algorithm="HS256")

    return token


async def create_token(person_id, expires_in: int = TOKEN_EXPIRATION_MINUTES, refresh: bool = False):
    data = {
        "person_id": person_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in),
        "iat": datetime.now(timezone.utc).timestamp()
    }
    if refresh:
        jti = str(uuid4())
        data['jti'] = jti

    token = jwt.encode(data, auth_secret, algorithm="HS256")

    return token
