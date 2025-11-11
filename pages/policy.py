from nicegui import ui
from frame import frame
from consts import support_email
from elements import page_header


@ui.page('/policy', title='Policy | Drop Dead Disco')
async def policy_page():
    async with frame(show_footer=False) as f:
        f.classes('px-4')
        page_header('Return Policy')

        ui.markdown(f'''
Any ticket purchased from [our website](/) may be refunded until the previous day (included) of the event it is designated for. 

The return process consists of the following steps: 

1. Contact support via [email](mailto:{support_email}) 
2. Your refund will be completed within 2-3 business days 
3. You'll receive your funds on the same card or account you made the purchase with 
    ''')
