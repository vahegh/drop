import os
import httpx
from consts import APP_BASE_URL
from api_models import VposInitPaymentRequest, VPOSPaymentDetailsResponse, VPOSPaymentDetailsRequest

VPOS_BASE_URL = os.environ["vpos_base_url"]
VPOS_CALLBACK_ENDPOINT = 'vpostransactionstate'
vpos_client_id = os.environ['vpos_client_id']
vpos_username = os.environ['vpos_username']
vpos_password = os.environ['vpos_password']


async def init_payment_vpos(order_id, amount, description=""):
    init = VposInitPaymentRequest(
        ClientID=vpos_client_id,
        Username=vpos_username,
        Password=vpos_password,
        Amount=amount,
        OrderID=order_id,
        Description=description,
        BackURL=f"{APP_BASE_URL}/{VPOS_CALLBACK_ENDPOINT}")

    async with httpx.AsyncClient() as client:
        req = init.model_dump(exclude_unset=True)
        req_url = f"{VPOS_BASE_URL}/api/VPOS/InitPayment"
        response = await client.post(req_url, json=req)
        response.raise_for_status()
        payment_id = response.json()['PaymentID']
        return payment_id


async def get_payment_details_vpos(payment_id):
    data = VPOSPaymentDetailsRequest(
        Username=vpos_username,
        Password=vpos_password,
        PaymentID=payment_id
    ).model_dump(mode='json')

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{VPOS_BASE_URL}/api/VPOS/GetPaymentDetails", json=data)
        response.raise_for_status()
        payment_data = VPOSPaymentDetailsResponse(**response.json())
        return payment_data
