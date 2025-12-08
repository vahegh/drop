import os
import httpx
from tempfile import NamedTemporaryFile
from api_models import ECRMPrintRequest, ECRMResponse, ECRMCheckConnRequest
import logging

logger = logging.getLogger(__name__)

ecrm_base_url = os.environ['ecrm_base_url']
ecrm_cert_pem = os.environ['ecrm_cert_pem']
ecrm_key_pem = os.environ['ecrm_key_pem']


async def ecrm_request(body, path):
    with NamedTemporaryFile(mode='w+b', delete_on_close=False) as cert_file, NamedTemporaryFile(mode='w+b', delete_on_close=False) as key_file:
        cert_file.write(ecrm_cert_pem.encode('utf-8'))
        cert_file.seek(0)
        key_file.write(ecrm_key_pem.encode('utf-8'))
        key_file.seek(0)

        async with httpx.AsyncClient(cert=(cert_file.name, key_file.name)) as client:
            resp = await client.post(f"{ecrm_base_url}/{path}", json=body, headers={"language": "en"})
            parsed_resp = ECRMResponse(**resp.json())
            if parsed_resp.code != 0:
                logger.error(f"Unable to make ECRM request: {parsed_resp.__dict__}")
            return parsed_resp


async def ecrm_print(print_request: ECRMPrintRequest):
    return await ecrm_request(body=print_request.model_dump(mode='json'), path='print')


async def ecrm_check_conn(check_request: ECRMCheckConnRequest):
    return await ecrm_request(body=check_request.model_dump(mode='json'), path='checkConnection')
