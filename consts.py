import os
import re
from zoneinfo import ZoneInfo

default_date_format = "%d.%m"
TIMEZONE = ZoneInfo('Asia/Yerevan')

APP_BASE_URL = os.environ['app_base_url']
APP_BASE_URL_NO_PROTO = os.environ['app_base_url_no_proto']
admins = os.environ['admins'].split()


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

APPLICATION_SUBMITTED_SUBJECT = "Application Submitted"
STATUS_CHANGE_SUBJECT = "Application Status Change"
MEMBER_PASS_SUBJECT = "Your Membership Pass"
EVENT_TICKET_SUBJECT = "Your Ticket For {event_name}"

IDRAM_PAYMENT_URL = os.environ["idram_payment_url"]
idram_merchant_id = os.environ["idram_merchant_id"]

DROP_SPOTIFY_URL = 'https://open.spotify.com/playlist/49t6kUgW6nB7Kcv4d357qy?si=e5527a59df38401f'
DROP_YOUTUBE_URL = 'https://www.youtube.com/@dropdeadisco'
google_client_id = '759529195467-d4dt9f5do5iu4g4itndu2v0q9vpmip93.apps.googleusercontent.com'
google_wallet_img_url = 'https://storage.googleapis.com/dropdeadisco/images/add_to_google.svg'
apple_wallet_img_url = 'https://storage.googleapis.com/dropdeadisco/images/add_to_apple.svg'

logo_gray_path = os.path.relpath("/static/images/logo_gray.png")


name_regex = r'^[a-zA-Z\s-]+$'
email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+$'
gmail_regex = r'^[a-zA-Z0-9_.+-]+@gmail\.com$'
insta_regex = r'^([A-Za-z0-9_](?:(?:[A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_]))?)$'

name_validation = {
    'Field is required': lambda value: value,
    'Name can only contain letters, spaces and hyphens': lambda value: re.match(name_regex, value)
}

email_validation = {
    'Field is required': lambda value: value,
    'Please enter a valid email address': lambda value: re.match(email_regex, value)
}

gmail_validation = {
    'Field is required': lambda value: value,
    'Please enter a valid Gmail address': lambda value: re.match(gmail_regex, value)
}

insta_validation = {
    'Field is required': lambda value: value,
    'Please enter a valid Instagram username': lambda value: re.match(insta_regex, value)
}

email_non_required = {
    'Please enter a valid email address': lambda value: re.match(email_regex, value)
}

email_placeholder = "johndoe@gmail.com"
instagram_placeholder = "johndoe123"

support_email = "dropdeadisco@gmail.com"


google_calendar_img_url = "https://upload.wikimedia.org/wikipedia/commons/a/a5/Google_Calendar_icon_%282020%29.svg"
calendar_base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
