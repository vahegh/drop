import time
import httpx
from uuid import UUID
from datetime import datetime
from google.auth import jwt
from google.auth.credentials import TokenState
from services.google_auth import get_google_credentials
from consts import ORG_NAME, MEMBER_PASS_TITLE, DROP_INSTA_URL, DROP_INSTA_TEXT, APP_BASE_URL
from google.auth.transport.requests import Request


async def get_token():
    credentials = await get_google_credentials(['https://www.googleapis.com/auth/wallet_object.issuer'])
    if not credentials.token_state == TokenState.FRESH:
        credentials.refresh(Request())
    return credentials.token


# DROP_HERO_IMAGE_URL = "https://storage.googleapis.com/dropdeadisco/images/DROP%20logo%20wide%20transparent.png"
DROP_LOGO_URL = "https://storage.googleapis.com/dropdeadisco/images/ticket_logo.png"
DROP_MEMBER_PASS_BG_COLOR = "#000000"
DROP_EVENT_TICKET_BG_COLOR = "#FFFFFF"
GOOGLE_PASS_BASE_URL = "https://walletobjects.googleapis.com/walletobjects/v1"
GOOGLE_ISSUER_ID = "3388000000022892625"


async def create_jwt(object_id):
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
    return encoded_jwt.decode('utf-8')


async def create_ticket_class(
        class_id: UUID,
        event_name: str,
        event_url: str,
        venue_name: str,
        venue_address: str,
        starts_at: datetime,
        ends_at: datetime,
        notify: bool = False
):

    body = {
        "id": f"{GOOGLE_ISSUER_ID}.{class_id}",
        "issuerName": ORG_NAME,
        'reviewStatus': 'UNDER_REVIEW',
        "hexBackgroundColor": DROP_EVENT_TICKET_BG_COLOR,
        "logo": {
            "sourceUri": {
                "uri": DROP_LOGO_URL,
            },
        },
        'eventName': {
            'defaultValue': {
                'language': 'en',
                'value': event_name
            }
        },
        "venue": {
            "name": {
                "defaultValue": {
                    "language": "en",
                    "value": venue_name
                }
            },
            "address": {
                "defaultValue": {
                    "language": "en",
                    "value": venue_address
                }
            }
        },
        "dateTime": {
            "start": starts_at.isoformat(),
            "end": ends_at.isoformat()
        },
        "securityAnimation": {
            "animationType": "FOIL_SHIMMER"
        },
        "linksModuleData": {
            "uris": [
                {
                    "description": "Event Info",
                    "uri": event_url
                }
            ]
        },
    }

    if notify:
        body['notifyPreference'] = "NOTIFY_ON_UPDATE"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{GOOGLE_PASS_BASE_URL}/eventTicketClass",
                                     headers={"Authorization": f"Bearer {await get_token()}"},
                                     json=body)
            if resp.status_code == 409:
                resp = await client.patch(f"{GOOGLE_PASS_BASE_URL}/eventTicketClass/{body['id']}",
                                          headers={"Authorization": f"Bearer {await get_token()}"},
                                          json=body)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(e.response.content)
        raise
    else:
        return resp.json()


async def update_member_class(class_id, event_name, event_url, venue_name, venue_maps_link, event_date, starts_at, ends_at, notify=False):
    google_member_pass_id = f"{GOOGLE_ISSUER_ID}.{class_id}"
    body = {
        "id": google_member_pass_id,
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

    if event_name:
        body['textModulesData'] = [
            {
                "header": "Next Event",
                "body": event_name,
                "id": "next_event_name"
            },
            {
                "header": "Date",
                "body": event_date,
                "id": "next_event_date"
            },
            {
                "header": "Start Time",
                "body": starts_at,
                "id": "next_event_start_time"
            },
            {
                "header": "End Time",
                "body": ends_at,
                "id": "next_event_end_time"
            },
            {
                "header": "Venue",
                "body": venue_name,
                "id": "next_event_venue"
            }
        ]

        links_data["uris"].insert(
            0,
            {
                "description": "Tickets and Information",
                "uri": event_url,
                "id": "event_url_back"
            }
        )

    body['linksModuleData'] = links_data

    async with httpx.AsyncClient() as client:
        update_resp = await client.patch(f"{GOOGLE_PASS_BASE_URL}/loyaltyClass/{google_member_pass_id}",
                                         headers={"Authorization": f"Bearer {await get_token()}"},
                                         json=body)
        update_resp.raise_for_status()
        return update_resp.json()


async def create_google_ticket(ticket_id, class_id, name):
    google_ticket_id = f"{GOOGLE_ISSUER_ID}.{ticket_id}"
    body = {
        'id': google_ticket_id,
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
            resp = await client.put(f"{GOOGLE_PASS_BASE_URL}/eventTicketObject/{google_ticket_id}",
                                    headers={"Authorization": f"Bearer {await get_token()}"},
                                    json=body)
        resp.raise_for_status()

    token = await create_jwt(google_ticket_id)
    return f'https://pay.google.com/gp/v/save/{token}'


async def create_google_member_pass(pass_id, class_id, member_no, name, attendance):
    google_member_pass_id = f"{GOOGLE_ISSUER_ID}.{pass_id}"
    body = {
        "id": google_member_pass_id,
        "classId": f"{GOOGLE_ISSUER_ID}.{class_id}",
        "state": "ACTIVE",
        "barcode": {
            "type": "QR_CODE",
            "value": pass_id,
            "alternateText": name
        },
        "accountName": name,
        "accountId": member_no,
        "loyaltyPoints": {
            "label": "Member ID",
            "balance": {
                "string": member_no,
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
            resp = await client.put(f"{GOOGLE_PASS_BASE_URL}/loyaltyObject/{google_member_pass_id}",
                                    headers={"Authorization": f"Bearer {await get_token()}"},
                                    json=body)
        resp.raise_for_status()

    token = await create_jwt(google_member_pass_id)
    return f'https://pay.google.com/gp/v/save/{token}'


async def patch_member_object(pass_id, body):
    google_member_pass_id = f"{GOOGLE_ISSUER_ID}.{pass_id}"
    async with httpx.AsyncClient() as client:
        patch_resp = await client.patch(f"{GOOGLE_PASS_BASE_URL}/loyaltyObject/{google_member_pass_id}",
                                        headers={"Authorization": f"Bearer {await get_token()}"},
                                        json=body)
    return patch_resp.json()


async def add_class_message(class_id, header, body, messageType="TEXT_AND_NOTIFY"):
    message = {
        "message": {
            "header": header,
            "body": body,
            "messageType": messageType
        }
    }
    async with httpx.AsyncClient() as client:
        try:
            msg = await client.post(f"{GOOGLE_PASS_BASE_URL}/eventTicketClass/{GOOGLE_ISSUER_ID}.{class_id}/addMessage",
                                    headers={"Authorization": f"Bearer {await get_token()}"},
                                    json=message)
            msg.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e.response.content)
        else:
            return msg
