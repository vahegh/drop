import os
import httpx
from services.myameria_auth import TokenManager
from api_models import MyAmeriaCreateRequest, MyAmeriaPaymentDetailsResponse, MyAmeriaPaymentDetailsRequest, MyAmeriaPaymentRefundRequest

token_manager = TokenManager()

MYAMERIA_BASE_URL = os.environ['myameria_base_url']
MYAMERIA_PAY_URL = os.environ['myameria_pay_url']
myameria_merchant_id = os.environ['myameria_merchant_id']


async def create_payment_myameria(order_id, amount):
    payment = MyAmeriaCreateRequest(
        transactionAmount=amount,
        transactionId=str(order_id),
        merchantId=myameria_merchant_id
    )

    async with httpx.AsyncClient() as client:
        req = payment.model_dump()
        response = await client.post(f"{MYAMERIA_BASE_URL}/Payment/CreatePayment", json=req, headers={"Authorization": f"Bearer {await token_manager.get_token()}"})
        response.raise_for_status()


async def get_payment_details_myameria(transaction_id, payment_id):
    data = MyAmeriaPaymentDetailsRequest(
        transactionId=transaction_id,
        paymentId=payment_id,
        merchantId=myameria_merchant_id
    ).model_dump(mode='json')

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MYAMERIA_BASE_URL}/Payment/Status", json=data, headers={"Authorization": f"Bearer {await token_manager.get_token()}"})
        response.raise_for_status()
        payment_data = MyAmeriaPaymentDetailsResponse(**response.json())
        return payment_data


async def refund_payment_myameria(request: MyAmeriaPaymentRefundRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MYAMERIA_BASE_URL}/Payment/Refund", json=request.model_dump(mode='json'), headers={"Authorization": f"Bearer {await token_manager.get_token()}"})
        response.raise_for_status()
        payment_data = MyAmeriaPaymentDetailsResponse(**response.json())
        return payment_data
