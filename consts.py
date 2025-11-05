from dotenv import load_dotenv
import os
import re
from zoneinfo import ZoneInfo

if os.path.exists('.env'):
    load_dotenv()

env = os.getenv('env')

TIMEZONE = ZoneInfo('Asia/Yerevan')

APP_BASE_URL = "https://dropdeadisco.com"
APP_BASE_URL_NO_PROTO = "dropdeadisco.com"


GOOGLE_MEMBER_CLASS_ID = "drop_member_pass"

ORG_NAME = "Drop Dead Disco"
MEMBER_PASS_TITLE = "Membership Pass"
DROP_INSTA_URL = "https://www.instagram.com/dropdeadisco/"
DROP_INSTA_TEXT = "Drop Dead Disco on Instagram"


APPLICATION_SUBMITTED_TEMPLATE = "submitted.html"
APPROVED_TEMPLATE = "approved.html"
REJECTED_TEMPLATE = "rejected.html"
MEMBER_PASS_TEMPLATE = "member_pass.html"
EVENT_TICKET_TEMPLATE = "event_ticket.html"
EVENT_ANNOUNCEMENT_TEMPLATE = "event_announcement.html"
VENUE_REVEAL_TEMPLATE = "venue_reveal.html"
MAGIC_LINK_TEMPLATE = "magic_link.html"

APPLICATION_SUBMITTED_SUBJECT = "Application Submitted"
STATUS_CHANGE_SUBJECT = "Application Status Change"
MEMBER_PASS_SUBJECT = "Your Membership Pass"
EVENT_TICKET_SUBJECT = "Your Ticket For {event_name}"
MAGIC_LINK_SUBJECT = "Your Payment Link"

IDRAM_PAYMENT_URL = os.environ["idram_payment_url"]
idram_merchant_id = os.environ["idram_merchant_id"]

DROP_SPOTIFY_URL = 'https://open.spotify.com/playlist/49t6kUgW6nB7Kcv4d357qy?si=e5527a59df38401f'
DROP_YOUTUBE_URL = 'https://www.youtube.com/@dropdeadisco'
app_base_url = os.environ['app_base_url']
google_client_id = '759529195467-d4dt9f5do5iu4g4itndu2v0q9vpmip93.apps.googleusercontent.com'
google_wallet_img_url = 'https://storage.googleapis.com/dropdeadisco/images/add_to_google.svg'
apple_wallet_img_url = 'https://storage.googleapis.com/dropdeadisco/images/add_to_apple.svg'

logo_white_path = os.path.relpath("static/images/logo_white.png")
logo_black_path = os.path.relpath("static/images/logo_black.png")
logo_gray_path = os.path.relpath("static/images/logo_gray.png")
favicon_path = os.path.relpath("static/images/favicon.png")
spotify_logo_path = os.path.relpath("static/images/spotify.svg")
instagram_logo_path = os.path.relpath("static/images/instagram.svg")
youtube_logo_path = os.path.relpath("static/images/youtube.svg")


album_urls = {
    '1470f7b7-0f21-4ef4-84e9-639ced8e692f': "https://photos.google.com/share/AF1QipPn4b0BCUT5qGC0Nqwy2jMZQS-w88tg6jKiyRbZWzkDd7VWASeavmKCJSWtDpaFlg?key=UG5WWS1pMFAyaHVPR2dSd29HWUlIRGhYRlpUaGFR",
    '6deb74b2-6f66-4eef-9f69-56e0f8e1e8bb': "https://photos.google.com/share/AF1QipPLA4siefjMD3pMl3GJsEfVjT-BqtB6eEng2aLpOoPTpYi-KlEWnBUP_t0T-WtS0Q?key=U0tJaFpxb2RybldUb1ZtWG1rRVZDd0dGaEpUSjNn",
    '4c40ff61-50b3-48c8-84eb-51debe0bf5f0': "https://photos.google.com/share/AF1QipMJresCkkmy7nlBsh4bvb1jN6QgfhF1t_vs5ZfHwLXlKcn8g3B-vln8FPkIloxpYw?key=bWtMRnVsZGlCM01KWlBLRFV2T3ROYVhZSzRESGJ3"
}


name_regex = r'^[a-zA-Z\s-]+$'
email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+$'
insta_regex = r'^([A-Za-z0-9_](?:(?:[A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_]))?)$'

name_validation = {
    'Field is required': lambda value: value,
    'Name can only contain letters, spaces and hyphens': lambda value: re.match(name_regex, value)
}

email_validation = {
    'Field is required': lambda value: value,
    'Please enter a valid email address': lambda value: re.match(email_regex, value)
}

insta_validation = {
    'Field is required': lambda value: value,
    'Please enter a valid Instagram username': lambda value: re.match(insta_regex, value)
}

email_non_required = {
    'Please enter a valid email address': lambda value: re.match(email_regex, value)
}

email_placeholder = "johndoe@example.com"
instagram_placeholder = "johndoe123"

support_email = "dropdeadisco@gmail.com"


google_calendar_img_url = "https://upload.wikimedia.org/wikipedia/commons/a/a5/Google_Calendar_icon_%282020%29.svg"
calendar_base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
