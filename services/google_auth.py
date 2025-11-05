import os
import json
from google.oauth2 import service_account

service_account_credentials = os.environ["service_account_credentials"]


async def get_google_credentials(scopes: list[str] = None):
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(service_account_credentials),
        scopes=scopes
    )
    return credentials
