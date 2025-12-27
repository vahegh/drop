import os
import json
import shutil
import logging
import zipfile
import hashlib
import tempfile
import subprocess
from services.cloud_storage import upload_apple_pass
from consts import (ORG_NAME, MEMBER_PASS_TITLE, DROP_INSTA_URL,
                    DROP_INSTA_TEXT, APP_BASE_URL_NO_PROTO,
                    APP_BASE_URL)
from db_models import Event, Venue, MemberPass, EventTicket

logger = logging.getLogger(__name__)

APPLE_PASS_IMAGES_DIR = "apple-pass-images"
APPLE_AUTH_TOKEN = os.environ["apple_auth_token"]
APPLE_TEAM_ID = os.environ["apple_team_id"]
APPLE_APNS_KEY = os.environ["apple_apns_key"]
APPLE_APNS_KEY_ID = os.environ["apple_apns_key_id"]
APPLE_UPDATE_URL = f"{APP_BASE_URL}/api/passupdates/"
APPLE_PASS_TYPE_ID = "pass.com.vahe.drop1"

CERT_DATA = os.getenv("apple_pass_cert")
PASSKEY_DATA = os.getenv("apple_pass_key")
WWDR_DATA = os.getenv("apple_pass_wwdr")


async def create_and_sign_pkpass(pass_json_data: dict):
    with tempfile.TemporaryDirectory() as pass_temp_dir:

        cert_file_path = os.path.join(pass_temp_dir, "pass_certificate.pem")
        passkey_file_path = os.path.join(pass_temp_dir, "passkey.key")
        wwdr_file_path = os.path.join(pass_temp_dir, "wwdr.pem")
        pass_json_path = os.path.join(pass_temp_dir, "pass.json")

        icon_path = os.path.join(pass_temp_dir, "icon.png")
        icon_3x_path = os.path.join(pass_temp_dir, "icon@3x.png")
        logo_path = os.path.join(pass_temp_dir, "logo.png")
        logo_3x_path = os.path.join(pass_temp_dir, "logo@3x.png")
        strip_path = os.path.join(pass_temp_dir, "strip.png")

        with open(cert_file_path, 'w') as f:
            f.write(CERT_DATA)

        with open(passkey_file_path, 'w') as f:
            f.write(PASSKEY_DATA)

        with open(wwdr_file_path, 'w') as f:
            f.write(WWDR_DATA)

        with open(pass_json_path, 'w') as f:
            f.write(json.dumps(pass_json_data, indent=4))

        shutil.copy2(f"{APPLE_PASS_IMAGES_DIR}/icon.png", icon_path)
        shutil.copy2(f"{APPLE_PASS_IMAGES_DIR}/icon_3x.png", icon_3x_path)
        shutil.copy2(f"{APPLE_PASS_IMAGES_DIR}/strip.png", strip_path)

        if pass_json_data.get('storeCard'):
            shutil.copy2(f"{APPLE_PASS_IMAGES_DIR}/member_pass_logo.png", logo_path)
            shutil.copy2(f"{APPLE_PASS_IMAGES_DIR}/member_pass_logo_3x.png", logo_3x_path)
        else:
            shutil.copy2(f"{APPLE_PASS_IMAGES_DIR}/ticket_logo.png", logo_path)
            shutil.copy2(f"{APPLE_PASS_IMAGES_DIR}/ticket_logo_3x.png", logo_3x_path)

        file_paths = [icon_path, icon_3x_path, logo_path, logo_3x_path, strip_path, pass_json_path]

        manifest_path = create_or_update_manifest(pass_temp_dir, file_paths)

        file_paths.append(manifest_path)

        signature_path = generate_signature(
            pass_temp_dir, manifest_path, cert_file_path, passkey_file_path, wwdr_file_path)

        file_paths.append(signature_path)

        pkpass_output_path = f"{pass_json_data['serialNumber']}.pkpass"

        try:
            pkpass = create_pkpass(file_paths, pkpass_output_path)
        except Exception as e:
            logger.error(f"Couldn't create .pkpass: {str(e)}")

    return pkpass


def create_or_update_manifest(base_dir, files):
    manifest = {}
    for file_path in files:
        file_name = os.path.basename(file_path)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                sha1_hash = hashlib.file_digest(f, 'sha1').hexdigest()
                manifest[file_name] = sha1_hash
    manifest_path = os.path.join(base_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path


def generate_signature(base_dir, manifest_path, cert_pem, private_key, wwdr_pem):
    signature_path = os.path.join(base_dir, "signature")
    openssl_cmd = [
        "openssl", "smime", "-sign",
        "-in", manifest_path,
        "-out", signature_path,
        "-signer", cert_pem,
        "-inkey", private_key,
        "-certfile", wwdr_pem,
        "-outform", "DER",
        "-binary"
    ]
    result = subprocess.run(openssl_cmd, capture_output=True, text=True)
    if not result.returncode == 0:
        logger.error(f"Error generating signature: {result.stderr}")
    return signature_path


def create_pkpass(files, output_pass):
    with zipfile.ZipFile(output_pass, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            file_name = os.path.basename(file_path)
            if os.path.exists(file_path):
                zipf.write(file_path, file_name)
            else:
                logger.warning(f"{file_name} not found, skipping")
    return output_pass


async def create_apple_member(member_pass: MemberPass, name, attendance, event: Event = None, venue: Venue = None):
    if event and venue:
        starts_at = event.starts_at.astimezone().isoformat()
        ends_at = event.ends_at.astimezone().isoformat()
    pass_id = str(member_pass.id)
    serial_no = str(member_pass.serial_number).zfill(3)

    apple_member_json = {
        "formatVersion": 1,
        "webServiceURL": APPLE_UPDATE_URL,
        "authenticationToken": APPLE_AUTH_TOKEN,
        "passTypeIdentifier": APPLE_PASS_TYPE_ID,
        "teamIdentifier": APPLE_TEAM_ID,
        "serialNumber": pass_id,
        "organizationName": ORG_NAME,
        "description": MEMBER_PASS_TITLE,
        "barcodes": [
            {
                "message": pass_id,
                "format": "PKBarcodeFormatQR",
                "messageEncoding": "iso-8859-1"
            }
        ],
        "storeCard": {
            "headerFields": [
                {
                    "key": "header",
                    "label": "Member",
                    "value": name
                },
            ],
            "secondaryFields": [
                {
                    "key": "member_id",
                    "label": "Member ID",
                    "value": serial_no,
                    "textAlignment": "PKTextAlignmentLeft"

                },
                {
                    "key": "events_attended",
                    "label": "Events Attended",
                    "value": attendance,
                    "textAlignment": "PKTextAlignmentRight",
                    "changeMessage": "Events attended: %@"
                },
            ],
        },
        "backgroundColor": "rgb(0,0,0)",
        "foregroundColor": "rgb(255,255,255)",
        "labelColor": "rgb(255,255,255)"
    }
    back_fields = [
        {
            "label": "Member",
            "key": "holder_back",
            "value": name
        },
        {
            "label": "Member ID",
            "key": "member_id_back",
            "value": serial_no
        }
    ]
    if event and venue:
        back_fields.extend(
            [
                {
                    "label": "Next Event",
                    "value": event.name,
                    "key": "event_name_back",
                    "changeMessage": "%@ is now live. Details inside the pass."
                },
                {
                    "label": "Date",
                    "value": starts_at,
                    "key": "event_date",
                    "dateStyle": "PKDateStyleShort",
                },
                {
                    "label": "Start Time",
                    "value": starts_at,
                    "key": "event_start_time",
                    "timeStyle": "PKDateStyleShort"
                },
                {
                    "label": "End Time",
                    "value": ends_at,
                    "key": "event_end_time",
                    "timeStyle": "PKDateStyleShort"
                },
                {
                    "label": "Venue",
                    "value": venue.name,
                    "key": "venue_back",
                    "changeMessage": f"Location: %@"
                },
                {
                    "label": "Tickets",
                    "value": APP_BASE_URL_NO_PROTO,
                    "attributedValue": f'<a href={APP_BASE_URL}/event/{event.id}?utm_source=apple_wallet&utm_medium=pass&utm_campaign=event_{event.id}&utm_content=ticket_link>{APP_BASE_URL_NO_PROTO}</a>',
                    "key": "event_url_back",
                },
                {
                    "label": DROP_INSTA_TEXT,
                    "value": DROP_INSTA_URL,
                    "key": "instagram",
                },
            ]
        )

        if venue.latitude and venue.longitude:
            apple_member_json['locations'] = [
                {"latitude": venue.latitude, "longitude": venue.longitude}]

    apple_member_json['storeCard']['backFields'] = back_fields

    pass_filename = await create_and_sign_pkpass(apple_member_json)

    pass_url = await upload_apple_pass(pass_filename)
    os.remove(pass_filename)
    return pass_url


async def create_apple_ticket(name, event_ticket: EventTicket, event: Event, venue: Venue):
    starts_at = event.starts_at.astimezone().isoformat()
    ends_at = event.ends_at.astimezone().isoformat()
    pass_id = str(event_ticket.id)

    apple_ticket_json = {
        "formatVersion": 1,
        "webServiceURL": APPLE_UPDATE_URL,
        "authenticationToken": APPLE_AUTH_TOKEN,
        "passTypeIdentifier": APPLE_PASS_TYPE_ID,
        "teamIdentifier": APPLE_TEAM_ID,
        "serialNumber": pass_id,
        "organizationName": ORG_NAME,
        "description": f"One-time ticket for {event.name}",
        "relevantDates": [{'date': starts_at}],
        "locations": [{"latitude": venue.latitude, "longitude": venue.longitude}],
        "barcodes": [
            {
                "message": pass_id,
                "format": "PKBarcodeFormatQR",
                "messageEncoding": "iso-8859-1"
            }
        ],
        "eventTicket": {
            "headerFields": [
                {
                    "key": "header",
                    "label": "",
                    "value": "Event Ticket"
                },
            ],
            "secondaryFields": [
                {
                    "key": "event_name",
                    "label": "Event",
                    "value": event.name,
                    "textAlignment": "PKTextAlignmentLeft"
                },
                {
                    "key": "holder",
                    "label": "Ticket Holder",
                    "value": name,
                    "textAlignment": "PKTextAlignmentRight"
                },
            ],
            "auxiliaryFields": [
                {
                    "key": "start_date",
                    "label": "Date",
                    "value": starts_at,
                    "dateStyle": "PKDateStyleShort",
                    "textAlignment": "PKTextAlignmentLeft"
                },
                {
                    "key": "start_time",
                    "label": "Time",
                    "value": starts_at,
                    "timeStyle": "PKDateStyleShort",
                    "textAlignment": "PKTextAlignmentRight"
                },
            ],
            "backFields": [
                {
                    "key": "holder_back",
                    "label": "Ticket Holder",
                    "value": name
                },
                {
                    "key": "event_name_back",
                    "label": "Event",
                    "value": event.name
                },
                {
                    "key": "event_url_back",
                    "label": "Event Info",
                    "value": f"{APP_BASE_URL}/event/{event.id}?utm_source=apple_wallet&utm_medium=pass&utm_campaign=event_{event.id}&utm_content=ticket_link",
                    "attributedValue": f'<a href={APP_BASE_URL}/event/{event.id}?utm_source=apple_wallet&utm_medium=pass&utm_campaign=event_{event.id}&utm_content=ticket_link>{APP_BASE_URL_NO_PROTO}</a>',
                },
                {
                    "key": "event_date",
                    "label": "Date",
                    "value": starts_at,
                    "dateStyle": "PKDateStyleShort",
                },
                {
                    "key": "event_start_time",
                    "label": "Start Time",
                    "value": starts_at,
                    "timeStyle": "PKDateStyleShort"
                },
                {
                    "key": "event_end_time",
                    "label": "End Time",
                    "value": ends_at,
                    "timeStyle": "PKDateStyleShort"
                },
                {
                    "key": "venue_back",
                    "label": "Venue",
                    "value": venue.name,
                    "changeMessage": f"Location: %@"
                }
            ]
        },
        "backgroundColor": "rgb(255,255,255)",
        "foregroundColor": "rgb(0,0,0)",
    }

    pass_filename = await create_and_sign_pkpass(apple_ticket_json)

    pass_url = await upload_apple_pass(pass_filename)
    os.remove(pass_filename)
    return pass_url
