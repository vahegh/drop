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


DROP_SPOTIFY_URL = 'https://open.spotify.com/playlist/49t6kUgW6nB7Kcv4d357qy?si=e5527a59df38401f'
DROP_YOUTUBE_URL = 'https://www.youtube.com/@dropdeadisco'
google_client_id = '759529195467-d4dt9f5do5iu4g4itndu2v0q9vpmip93.apps.googleusercontent.com'
google_wallet_img_url = 'https://storage.googleapis.com/dropdeadisco/images/add_to_google.svg'
apple_wallet_img_url = 'https://storage.googleapis.com/dropdeadisco/images/add_to_apple.svg'

google_calendar_img_url = "https://upload.wikimedia.org/wikipedia/commons/a/a5/Google_Calendar_icon_%282020%29.svg"
calendar_base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"

all_photos_url = "https://photos.google.com/share/AF1QipNb8__JbXtuax9DJm21Ca666tb2o4voA1u09nj0Z04jhyNjfdzcQ-1KTMqI7N9zNA?key=MG11Qm01N1JRWGxZUElGazdvcGlzOEw4VWVobUdR"
