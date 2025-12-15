from google.cloud import storage
from services.google_auth import get_google_credentials
import base64

GCS_BUCKET_NAME = "dropdeadisco"
APPLE_PASSES_GCS_DIR = "apple_passes"
AVATARS_GCS_DIR = "avatars"


async def upload_apple_pass(filename: str) -> str:
    storage_client = storage.Client(credentials=await get_google_credentials())
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    blob = bucket.blob(f"{APPLE_PASSES_GCS_DIR}/{filename}")
    if blob.exists():
        blob.delete()
    blob.cache_control = "max-age=0"
    blob.upload_from_filename(filename)
    return blob.public_url


async def upload_avatar(filename: str, file_bytes: bytes, content_type: str) -> str:
    storage_client = storage.Client(credentials=await get_google_credentials())
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    blob = bucket.blob(f"{AVATARS_GCS_DIR}/{filename}")
    if blob.exists():
        blob.delete()
    blob.cache_control = "max-age=0"
    blob.upload_from_string(file_bytes, content_type=content_type)
    return blob.public_url


async def get_pass_file(serial_number: str):
    storage_client = storage.Client(credentials=await get_google_credentials())
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    blob = bucket.blob(f"{APPLE_PASSES_GCS_DIR}/{serial_number}.pkpass")
    if blob.exists():
        return blob.download_as_bytes()
    return None


async def get_event_img(filename):
    storage_client = storage.Client(credentials=await get_google_credentials())
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(f"event-images/{filename}")
    blob.cache_control = "max-age=0"
    if blob.exists():
        file_bytes = blob.download_as_bytes()
        return base64.b64encode(file_bytes).decode('utf-8')
    return None
