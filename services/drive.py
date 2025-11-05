import os
import json
import httpx
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from typing import Optional
from api_models import DriveFolder
from db_models import Person

PARENT_FOLDER_ID = '1vwXB7OzHku6OEzldfNHDvEiBg3XbQcyF'
DRIVE_API_URL = 'https://www.googleapis.com/drive/v3'

logger = logging.getLogger(__name__)


class DriveService:
    def __init__(self):
        creds_dict = json.loads(os.getenv('google_drive_creds'))
        self.creds = Credentials.from_authorized_user_info(creds_dict)
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient()
        logger.info("Created Google Drive service.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def _get_headers(self):
        if self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())
        return {'Authorization': f'Bearer {self.creds.token}'}

    async def create_drive_folder(self, person_id: str, member_name: str) -> DriveFolder:
        file_metadata = {
            'name': f"{member_name}'s photos",
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [PARENT_FOLDER_ID],
            'properties': {
                'person_id': str(person_id),
                'member_name': member_name
            }
        }

        response = await self.client.post(
            f'{DRIVE_API_URL}/files',
            headers=self._get_headers(),
            json=file_metadata,
            params={'fields': 'id, name, mimeType, webViewLink, properties'}
        )

        logger.info(f"Created drive folder for {member_name}.")
        item = response.json()
        return DriveFolder(
            id=item.get('id'),
            name=item.get('name'),
            mime_type=item.get('mimeType'),
            web_view_link=item.get('webViewLink'),
            person_id=person_id,
            member_name=member_name
        )

    async def share_folder_with_email(self, folder_id: str, email: str, role: str = 'reader') -> None:
        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email,
        }

        await self.client.post(
            f'{DRIVE_API_URL}/files/{folder_id}/permissions',
            headers=self._get_headers(),
            json=permission,
            params={'sendNotificationEmail': 'false'}
        )
        logger.info(f"Shared drive folder with {email}.")

    async def list_items_in_folder(self, parent_folder_id: str = PARENT_FOLDER_ID) -> list[DriveFolder]:
        query = f"'{parent_folder_id}' in parents and trashed=false"

        response = await self.client.get(
            f'{DRIVE_API_URL}/files',
            headers=self._get_headers(),
            params={
                'q': query,
                'spaces': 'drive',
                'fields': 'files(id, name, mimeType, webViewLink, properties)',
                'pageSize': 100
            }
        )

        items = response.json().get('files', [])
        return [
            DriveFolder(
                id=item.get('id'),
                name=item.get('name'),
                mime_type=item.get('mimeType'),
                web_view_link=item.get('webViewLink'),
                person_id=item.get('properties', {}).get('person_id'),
                member_name=item.get('properties', {}).get('member_name')
            )
            for item in items
        ]

    async def find_folder_by_person_id(self, person_id: str) -> Optional[DriveFolder]:
        query = f"properties has {{ key='person_id' and value='{person_id}' }}"

        response = await self.client.get(
            f'{DRIVE_API_URL}/files',
            headers=self._get_headers(),
            params={
                'q': query,
                'spaces': 'drive',
                'fields': 'files(id, name, mimeType, webViewLink, properties)'
            }
        )

        items = response.json().get('files', [])
        if not items:
            return None

        logger.info(f"Person id: {person_id}, folders: {[i['name'] for i in items]}.")

        item = items[0]
        return DriveFolder(
            id=item.get('id'),
            name=item.get('name'),
            mime_type=item.get('mimeType'),
            web_view_link=item.get('webViewLink'),
            person_id=item.get('properties', {}).get('person_id'),
            member_name=item.get('properties', {}).get('member_name')
        )

    async def create_and_share_folder(self, person: Person):
        drive_folder = await self.find_folder_by_person_id(person.id)
        if drive_folder:
            logger.info(f"{person.name} already has a folder: {drive_folder.name}")
        else:
            drive_folder = await self.create_drive_folder(person.id, person.name)
        await self.share_folder_with_email(drive_folder.id, person.email)

        return f"{drive_folder.web_view_link}?authuser={person.email}"


drive_service = DriveService()
