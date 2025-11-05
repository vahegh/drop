from google.cloud import storage
from services.google_auth import get_google_credentials

GCS_BUCKET_NAME = "dropdeadisco"
APPLE_PASSES_GCS_DIR = "apple_passes"


async def upload_apple_pass(filename) -> str:
    storage_client = storage.Client(credentials=await get_google_credentials())
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    blob = bucket.blob(f"{APPLE_PASSES_GCS_DIR}/{filename}")
    if blob.exists():
        blob.delete()
    blob.cache_control = "max-age=0"
    blob.upload_from_filename(filename)
    return blob.public_url


async def get_pass_file(serial_number: str):
    storage_client = storage.Client(credentials=await get_google_credentials())
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    blob = bucket.blob(f"{APPLE_PASSES_GCS_DIR}/{serial_number}.pkpass")
    if blob.exists():
        return blob.download_as_bytes()
    return None
