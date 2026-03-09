import time
import httpx
import logging
from google.auth import jwt
from google.auth.credentials import TokenState
from services.google_auth import get_google_credentials
from consts import ORG_NAME, MEMBER_PASS_TITLE, DROP_INSTA_URL, DROP_INSTA_TEXT, APP_BASE_URL
from google.auth.transport.requests import Request
from db_models import Venue, Event, MemberPass

logger = logging.getLogger(__name__)

GOOGLE_MEMBER_CLASS_ID = "drop_member_pass"
DROP_LOGO_URL = "https://storage.googleapis.com/dropdeadisco/images/ticket_logo.png"
DROP_MEMBER_PASS_BG_COLOR = "#000000"
DROP_EVENT_TICKET_BG_COLOR = "#FFFFFF"
GOOGLE_PASS_BASE_URL = "https://walletobjects.googleapis.com/walletobjects/v1"
GOOGLE_ISSUER_ID = "3388000000022892625"


async def get_token():
    credentials = await get_google_credentials(['https://www.googleapis.com/auth/wallet_object.issuer'])
    if not credentials.token_state == TokenState.FRESH:
        credentials.refresh(Request())
    return credentials.token


async def create_signed_pass_url(object_id):
    credentials = await get_google_credentials(['https://www.googleapis.com/auth/wallet_object.issuer'])
    jwt_payload = {
        "iss": credentials.service_account_email,
        "aud": "google",
        "typ": "savetowallet",
        "iat": int(time.time()),
        "payload": {
            "eventTicketObjects": [
                {
                    "id": object_id
                }
            ]
        },
        "origins": [APP_BASE_URL]
    }

    encoded_jwt = jwt.encode(
        credentials.signer,
        jwt_payload,
    )
    return f"https://pay.google.com/gp/v/save/{encoded_jwt.decode('utf-8')}"


async def create_ticket_class(event: Event, venue: Venue):
    class_id = f"{GOOGLE_ISSUER_ID}.{event.id}"

    body = {
        "id": class_id,
        "issuerName": ORG_NAME,
        "reviewStatus": "UNDER_REVIEW",
        "hexBackgroundColor": DROP_EVENT_TICKET_BG_COLOR,
        "logo": {
            "sourceUri": {
                "uri": DROP_LOGO_URL,
            },
        },
        'eventName': {
            'defaultValue': {
                'language': 'en',
                'value': event.name
            }
        },
        "venue": {
            "name": {
                "defaultValue": {
                    "language": "en",
                    "value": venue.name
                }
            },
            "address": {
                "defaultValue": {
                    "language": "en",
                    "value": venue.address
                }
            }
        },
        "dateTime": {
            "start": event.starts_at.astimezone().isoformat(),
            "end": event.ends_at.astimezone().isoformat()
        },
        "securityAnimation": {
            "animationType": "FOIL_SHIMMER"
        },
        "linksModuleData": {
            "uris": [
                {
                    "description": "Event Info",
                    "uri": f"{APP_BASE_URL}/event/{event.id}?utm_source=google_wallet&utm_medium=pass&utm_campaign=event_{event.id}&utm_content=ticket_link"
                },
                {
                    "description": "Google Maps",
                    "uri": venue.google_maps_link,
                },
                {
                    "description": "Yandex Maps",
                    "uri": venue.yandex_maps_link,
                }

            ]
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{GOOGLE_PASS_BASE_URL}/eventTicketClass",
                                     headers={"Authorization": f"Bearer {await get_token()}"},
                                     json=body)
            if resp.status_code == 409:
                resp = await client.patch(f"{GOOGLE_PASS_BASE_URL}/eventTicketClass/{class_id}",
                                          headers={"Authorization": f"Bearer {await get_token()}"},
                                          json=body)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(f"Unable to create ticket class: {e.response.content}")
        raise
    else:
        return resp.json()


async def update_member_class(event: Event = None, venue: Venue = None):
    class_id = f"{GOOGLE_ISSUER_ID}.{GOOGLE_MEMBER_CLASS_ID}"

    body = {
        "id": class_id,
        "issuerName": ORG_NAME,
        'reviewStatus': 'UNDER_REVIEW',
        "hexBackgroundColor": DROP_MEMBER_PASS_BG_COLOR,
        "programName": MEMBER_PASS_TITLE,
        "programLogo": {
            "sourceUri": {
                "uri": DROP_LOGO_URL,
            },
        },
        "securityAnimation": {
            "animationType": "FOIL_SHIMMER"
        }
    }
    links_data = {
        "uris": [
            {
                "description": DROP_INSTA_TEXT,
                "uri": DROP_INSTA_URL,
                "id": "instagram"
            }
        ]
    }

    if event:
        body['textModulesData'] = [
            {
                "header": "Next Event",
                "body": event.name,
                "id": "next_event_name"
            },
            {
                "header": "Date",
                "body": event.starts_at.astimezone().strftime("%B %d, %Y"),
                "id": "next_event_date"
            },
            {
                "header": "Start Time",
                "body": event.starts_at.astimezone().strftime('%H:%M'),
                "id": "next_event_start_time"
            },
            {
                "header": "End Time",
                "body": event.ends_at.astimezone().strftime('%H:%M'),
                "id": "next_event_end_time"
            },
        ]

        links_data["uris"].insert(
            0,
            {
                "description": "Tickets and Information",
                "uri": f"{APP_BASE_URL}/event/{event.id}?utm_source=google_wallet&utm_medium=pass&utm_campaign=event_{event.id}&utm_content=ticket_link",
                "id": "event_url_back"
            }
        )

    if venue:
        body['textModulesData'].append(
            {
                "header": "Venue",
                "body": venue.name,
                "id": "next_event_venue"
            }
        )
        links_data["uris"].append(
            {
                "description": "Google Maps",
                "uri": venue.google_maps_link,
                "id": "google_maps_url_back"
            }
        )
        links_data["uris"].append(
            {
                "description": "Yandex Maps",
                "uri": venue.yandex_maps_link,
                "id": "yandex_maps_url_back"
            }
        )

    body['linksModuleData'] = links_data

    async with httpx.AsyncClient() as client:
        update_resp = await client.patch(f"{GOOGLE_PASS_BASE_URL}/loyaltyClass/{class_id}",
                                         headers={"Authorization": f"Bearer {await get_token()}"},
                                         json=body)
        update_resp.raise_for_status()
        return update_resp.json()


async def create_google_ticket(ticket_id, class_id, name):
    id = f"{GOOGLE_ISSUER_ID}.{ticket_id}"

    body = {
        'id': id,
        'classId': f"{GOOGLE_ISSUER_ID}.{class_id}",
        'state': 'ACTIVE',
        'ticketHolderName': name,
        'barcode': {
            "type": "QR_CODE",
            "value": ticket_id,
            "alternateText": name,
        },
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{GOOGLE_PASS_BASE_URL}/eventTicketObject",
                                 headers={"Authorization": f"Bearer {await get_token()}"},
                                 json=body)
        if resp.status_code == 409:
            resp = await client.put(f"{GOOGLE_PASS_BASE_URL}/eventTicketObject/{id}",
                                    headers={"Authorization": f"Bearer {await get_token()}"},
                                    json=body)
        resp.raise_for_status()

    return await create_signed_pass_url(id)


async def create_google_member_pass(name, attendance, member_pass: MemberPass):
    id = f"{GOOGLE_ISSUER_ID}.{member_pass.id}"
    serial_no = str(member_pass.serial_number).zfill(3)

    body = {
        "id": id,
        "classId": f"{GOOGLE_ISSUER_ID}.{GOOGLE_MEMBER_CLASS_ID}",
        "state": "ACTIVE",
        "barcode": {
            "type": "QR_CODE",
            "value": str(member_pass.id),
            "alternateText": name
        },
        "accountName": name,
        "accountId": serial_no,
        "loyaltyPoints": {
            "label": "Member ID",
            "balance": {
                "string": serial_no,
            },
        },
        "secondaryLoyaltyPoints": {
            "label": "Events Attended",
            "balance": {
                "string": attendance,
            },
        },

    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{GOOGLE_PASS_BASE_URL}/loyaltyObject",
                                 headers={"Authorization": f"Bearer {await get_token()}"},
                                 json=body)
        if resp.status_code == 409:
            resp = await client.put(f"{GOOGLE_PASS_BASE_URL}/loyaltyObject/{id}",
                                    headers={"Authorization": f"Bearer {await get_token()}"},
                                    json=body)
        resp.raise_for_status()

    return await create_signed_pass_url(id)


async def patch_member_object(pass_id, body):
    google_member_pass_id = f"{GOOGLE_ISSUER_ID}.{pass_id}"
    async with httpx.AsyncClient() as client:
        patch_resp = await client.patch(f"{GOOGLE_PASS_BASE_URL}/loyaltyObject/{google_member_pass_id}",
                                        headers={"Authorization": f"Bearer {await get_token()}"},
                                        json=body)
    return patch_resp.json()


async def add_class_message(class_id, header, body, message_type="TEXT_AND_NOTIFY"):
    message = {
        "message": {
            "header": header,
            "body": body,
            "messageType": message_type
        }
    }
    async with httpx.AsyncClient() as client:
        try:
            msg = await client.post(f"{GOOGLE_PASS_BASE_URL}/eventTicketClass/{GOOGLE_ISSUER_ID}.{class_id}/addMessage",
                                    headers={"Authorization": f"Bearer {await get_token()}"},
                                    json=message)
            msg.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Unable to add class message: {e.response.content}")
        else:
            return msg
