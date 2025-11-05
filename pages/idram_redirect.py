from nicegui import ui
from consts import idram_merchant_id, idram_payment_url
from fastapi.responses import HTMLResponse


@ui.page("/idram-payment")
async def idram_payment(order_id: str, amount: int, description: str):

    html = f"""
    <html>
    <body onload="document.forms[0].submit()">
      <form action="{idram_payment_url}" method="POST">
        <input type="hidden" name="EDP_LANGUAGE" value="EN">
        <input type="hidden" name="EDP_REC_ACCOUNT" value="{idram_merchant_id}">
        <input type="hidden" name="EDP_DESCRIPTION" value="{description}">
        <input type="hidden" name="EDP_AMOUNT" value="{amount}">
        <input type="hidden" name="EDP_BILL_NO" value="{order_id}">
      </form>
      <p>Redirecting to Idram...</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
