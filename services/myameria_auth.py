import os
import time
import httpx
from typing import Optional
from pydantic import BaseModel
from fastapi import HTTPException

MYAMERIA_AUTH_URL = os.environ['myameria_auth_url']
myameria_client_id = os.environ['myameria_client_id']
myameria_client_secret = os.environ['myameria_client_secret']

GRANT_TYPE = "client_credentials"


class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str


class TokenManager:
    def __init__(self):
        self.token: Optional[TokenResponse] = None
        self.expiry_time: float = 0.0

    async def get_token(self) -> str:
        if self.token and time.time() < self.expiry_time - 10:
            return self.token.access_token

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    MYAMERIA_AUTH_URL,
                    data={
                        "client_id": myameria_client_id,
                        "client_secret": myameria_client_secret,
                        "grant_type": GRANT_TYPE,
                    }
                )
                response.raise_for_status()
                token_data = TokenResponse(**response.json())
                self.token = token_data
                self.expiry_time = time.time() + token_data.expires_in
                return token_data.access_token
            except httpx.HTTPError as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch token: {str(e)}")
