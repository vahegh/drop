from fastapi import HTTPException
from api_models import (VPOSInitPaymentRequest, VPOSPaymentDetailsResponse,
                        VPOSPaymentDetailsRequest, VPOSBindingsRequest,
                        VPOSBindingsResponse, VPOSDeactivateBindingRequest,
                        VPOSMakeBindingPaymentRequest, VPOSMakeBindingPaymentResponse,
                        VPOSCancelPaymentRequest, VPOSCancelPaymentResponse)
from consts import APP_BASE_URL
import os
import logging
import httpx
from uuid import uuid4

logger = logging.getLogger(__name__)

VPOS_BASE_URL = os.environ["vpos_base_url"]
VPOS_CALLBACK_ENDPOINT = 'callback/vpos'
vpos_client_id = os.environ['vpos_client_id']
vpos_username = os.environ['vpos_username']
vpos_password = os.environ['vpos_password']


async def make_binding_payment_vpos(
    binding_id,
    order_id,
    amount,
    description=""
):
    request = VPOSMakeBindingPaymentRequest(
        ClientID=vpos_client_id,
        Username=vpos_username,
        Password=vpos_password,
        Amount=amount,
        OrderID=order_id,
        Description=description,
        BackURL="",
        CardHolderID=binding_id,
        Opaque=binding_id
    )

    async with httpx.AsyncClient() as client:
        req_url = f"{VPOS_BASE_URL}/api/VPOS/MakeBindingPayment"
        response = await client.post(req_url, json=request.model_dump(mode='json'))
        response.raise_for_status()
        return VPOSMakeBindingPaymentResponse(**response.json())


async def init_payment_vpos(
        order_id,
        amount,
        description="",
        back_url=f"{APP_BASE_URL}/{VPOS_CALLBACK_ENDPOINT}",
        save_card=False
):

    cardholder_id = uuid4() if save_card else None

    request = VPOSInitPaymentRequest(
        ClientID=vpos_client_id,
        Username=vpos_username,
        Password=vpos_password,
        Amount=amount,
        OrderID=order_id,
        Description=description,
        BackURL=back_url,
        CardHolderID=cardholder_id,
        Opaque=cardholder_id
    ).model_dump(exclude_unset=True, exclude_none=True, mode='json')

    async with httpx.AsyncClient() as client:
        req_url = f"{VPOS_BASE_URL}/api/VPOS/InitPayment"
        response = await client.post(req_url, json=request)
        response.raise_for_status()
        payment_id = response.json()['PaymentID']
        return payment_id


async def get_payment_details_vpos(payment_id):
    request = VPOSPaymentDetailsRequest(
        Username=vpos_username,
        Password=vpos_password,
        PaymentID=payment_id
    ).model_dump(mode='json')

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{VPOS_BASE_URL}/api/VPOS/GetPaymentDetails", json=request)
        response.raise_for_status()
        payment_data = VPOSPaymentDetailsResponse(**response.json())
        return payment_data


async def get_card_binding_vpos(binding_id):
    request = VPOSBindingsRequest(
        ClientID=vpos_client_id,
        Username=vpos_username,
        Password=vpos_password,
    ).model_dump(mode='json')

    async with httpx.AsyncClient() as client:
        req_url = f"{VPOS_BASE_URL}/api/VPOS/GetBindings"
        response = await client.post(req_url, json=request)
        response.raise_for_status()
        cards = VPOSBindingsResponse(**response.json())
        card_binding = next(
            (item for item in cards.CardBindingFileds if item.CardHolderID == binding_id), None)
        return card_binding


async def deactivate_binding_vpos(id):
    request = VPOSDeactivateBindingRequest(
        ClientID=vpos_client_id,
        Username=vpos_username,
        Password=vpos_password,
        CardHolderID=id
    ).model_dump(mode='json')

    async with httpx.AsyncClient() as client:
        req_url = f"{VPOS_BASE_URL}/api/VPOS/DeactivateBinding"
        response = await client.post(req_url, json=request)
        response.raise_for_status()
        return response


async def cancel_payment_vpos(id):
    async with httpx.AsyncClient() as client:
        request = VPOSCancelPaymentRequest(
            Username=vpos_username,
            Password=vpos_password,
            PaymentID=id
        )
        req_url = f"{VPOS_BASE_URL}/api/VPOS/CancelPayment"
        response = await client.post(req_url, json=request.model_dump(mode='json'))
        response.raise_for_status()
        response = VPOSCancelPaymentResponse(**response.json())
        if response.ResponseCode != "00":
            logger.error(
                f"VPOS CancelPayment failed: code={response.ResponseCode} message={response.ResponseMessage} payment_id={id}")
            raise HTTPException(400, response.ResponseMessage)
        return response
