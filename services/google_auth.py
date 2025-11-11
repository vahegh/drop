import os
import json
from google.oauth2 import service_account
import httpx

service_account_credentials = os.environ["service_account_credentials"]


async def get_google_credentials(scopes: list[str] = None):
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(service_account_credentials),
        scopes=scopes
    )
    return credentials


async def google_login():
    async with httpx.AsyncClient() as client:
        resp = client.get("""
https://accounts.google.com/o/oauth2/v2/auth?
 response_type=code&
 client_id=759529195467-d4dt9f5do5iu4g4itndu2v0q9vpmip93.apps.googleusercontent.com&
 scope=openid email profile&
 redirect_uri=&
 state=security_token%3D138r5719ru3e1%26url%3Dhttps%3A%2F%2Foauth2-login-demo.example.com%2FmyHome&
""")
