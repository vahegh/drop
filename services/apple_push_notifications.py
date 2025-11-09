import logging
from sqlalchemy import select
from aioapns.common import PRIORITY_NORMAL
from sqlalchemy.ext.asyncio import AsyncSession
from aioapns import APNs, NotificationRequest, PushType
from db_models import AppleDeviceRegistrations, AppleDevices
from services.apple_pass import APPLE_APNS_KEY, APPLE_APNS_KEY_ID, APPLE_TEAM_ID, APPLE_PASS_TYPE_ID
from decorators import with_db

logger = logging.getLogger(__name__)


async def apple_send_push_notification(device_token: str):
    apns_client = APNs(
        key=APPLE_APNS_KEY,
        key_id=APPLE_APNS_KEY_ID,
        team_id=APPLE_TEAM_ID,
        topic=APPLE_PASS_TYPE_ID,
        use_sandbox=False
    )
    request = NotificationRequest(
        device_token=device_token,
        message={},
        push_type=PushType.BACKGROUND,
        priority=PRIORITY_NORMAL
    )
    try:
        response = await apns_client.send_notification(request)
        if not response.is_successful:
            logger.warning(f"Failed to send notification to {device_token}: {response.description}")
    except Exception as e:
        logger.warning(f"Error sending notification to {device_token}: {str(e)}")


@with_db
async def apple_notify_pass_devices(db: AsyncSession, serial_number: str):
    registrations = await db.execute(
        select(AppleDeviceRegistrations.device_id).where(
            AppleDeviceRegistrations.serial_number == serial_number)
    )
    device_ids = [row[0] for row in registrations.fetchall()]
    if not device_ids:
        return

    devices = await db.execute(
        select(AppleDevices).where(AppleDevices.device_id.in_(device_ids))
    )
    for device in devices.scalars():
        await apple_send_push_notification(device.push_token)
