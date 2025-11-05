from nicegui import ui
from frame import frame
from elements import secondary_button, page_header, section_title
from helpers import set_user_data


@ui.page('/about', title='About Us | Drop Dead Disco')
async def about_page():
    async with frame() as main_col:
        main_col.classes('gap-4 p-6')
        logged_in = await set_user_data()

        with ui.column().classes('gap-2'):
            page_header('About Us')
            ui.markdown('''
**Drop Dead Disco** is a dance music community for those who want more from a night out. 

We host our events in unexpected locations - whatever has the most sparkle. 
                    
We don't tell you the location beforehand, and every guest has to pass **verification** before they're able to buy tickets and attend.
''').classes('text-md/5')

        with ui.column().classes('gap-0'):
            section_title("Verification?")
            ui.markdown('''
Yes. 
                    
The reason we started this was to gather like-minded people around the thing we love the most - **music**.
                        
We want to make sure that everyone gets that. Thus, we are very strict about who we let in.

We review you through your Instagram account. We don't share your information.

Once you've become a regular and proven to be a part of the community, we may invite you to become a **Member**.
''')

        with ui.column().classes('gap-0'):
            section_title("Who are the Members?")
            ui.markdown('''
**Members** are the heart and soul of Drop Dead Disco - without them this couldn't happen.

As such, they get more benefits like:

- Free or discounted event access

- Special digital cards with their serial no. and number of events attended

- Member-only events
''')

        with ui.column().classes('gap-0'):
            section_title("What to expect?")
            ui.markdown('''
First, the location will be revealed 24h before the start of the event, only to members and ticket holders.

It's likely that it will be your first time there, and that you'll love it.
                        
Almost certainly, you'll meet some people who you'll connect with, and want to keep in touch.
                        
You'll hear some of your favourite tracks (even ones you had forgotten about), and some new bangers.
''')

        with ui.column().classes('gap-0'):
            section_title("How do I get in?")
            ui.markdown('''
1. Tap the button below and sign up.

2. As soon as you sign up, we get notified and the review process begins.

3. You'll be notified about your status in 24 hours.
If approved, you'll be able to buy tickets for upcoming events.
''')

        ui.markdown('''
If there are no planned events at the time of your approval, you're still in, and will get future event updates as they are available.
''')
        if not logged_in:
            with ui.column().classes('gap-0'):
                section_title("Wanna join the fun?")
                ui.label("Sign up to get verified.")
            ui.html('''
                    <div class="g_id_signin"
                        data-type="standard"
                        data-shape="pill"
                        data-theme="filled_blue"
                        data-text="continue_with"
                        data-size="large"
                        data-locale="en-US"
                        data-logo_alignment="left">
                    </div>''', sanitize=False).classes('h-[32px]')
