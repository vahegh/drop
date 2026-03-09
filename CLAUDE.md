# DROP Dead Disco — CLAUDE.md

## Project Overview
Full-stack event management and ticketing platform for a nightclub venue in Yerevan, Armenia.
Production: https://dropdeadisco.com — deployed on Google Cloud Run.

## Tech Stack
- **UI:** NiceGUI (Python-based reactive web UI, no JavaScript framework)
- **API:** FastAPI + Starlette (ASGI)
- **DB:** PostgreSQL (async via asyncpg) + SQLAlchemy (async ORM) + Alembic migrations
- **Auth:** Google OAuth → JWT (15-min access token + 7-day refresh, cookie-based)
- **Payments:** VPOS, MyAmeria, IDRAM, Apple Pay, Google Pay, Card Binding
- **Passes:** Apple Wallet (PKPass + APN push updates), Google Pay (JWT-based)
- **Notifications:** aiosmtplib (email) + Telegram bot
- **Cloud:** Google Cloud Storage, Google Cloud Run, Cloud Build CI/CD
- **Runtime:** Python 3.13

## Project Structure
```
main.py               # Entry point — NiceGUI server, middleware, route registration
db.py                 # Async PostgreSQL engine (pool 10+5, 3600s recycle)
db_models.py          # SQLAlchemy ORM models
api_models.py         # Pydantic request/response models
enums.py              # PersonStatus, PaymentStatus, PaymentProvider
consts.py             # Email addresses, templates, regexes, URLs
dependencies.py       # AuthMiddleware (cookie-based auth, request.state injection)
components.py         # Reusable NiceGUI UI widgets (30+)
frame.py              # Page layout wrapper
storage_cache.py      # In-memory cache, 120-min TTL
helpers.py            # Utility functions (user agent, analytics)
decorators.py         # @with_db decorator

pages/                # NiceGUI UI pages (home, event, buy_ticket, profile, admin, etc.)
routes/               # FastAPI endpoints (auth, attendance, apple_pass_updates, event, telegram_webhook)
services/             # Business logic (25+ modules)
migrations/           # Alembic schema versions (50+)
templates/            # Jinja2 HTML email templates
static/               # Images, bg_video.mp4, favicon
apple-pass-images/    # Apple Wallet pass assets
```

## Database Models
- `Venue` — event locations
- `Person` — users (status: pending/verified/rejected/member)
- `Event` — events with pricing tiers (early_bird, general_admission, member)
- `MemberPass` — one per person, links to Apple/Google pass URLs
- `EventTicket` — one per (person, event), tracks attended_at
- `Payment` — orders (BigInteger order_id, multi-provider)
- `PaymentIntent` — async payment tracking
- `RefreshToken` — JWT refresh tokens
- `CardBinding` — stored card data for 1-click payments
- `Drink` / `DrinkVoucher` / `DrinkPaymentIntent` — drink voucher system
- `AppleDevices` / `AppleDeviceRegistrations` — Apple Wallet push tracking

All PKs are UUIDs (`gen_random_uuid()`). No hard deletes — status changes only.

## Environment Variables
- `db_conn_string` — PostgreSQL async connection string (required at startup)
- `storage_secret` — NiceGUI session storage secret
- `env` — set to `"local"` to disable Meta Pixel and other production-only features

## Running Locally
```bash
# Requires a .env file with db_conn_string and storage_secret
python main.py
```
App starts on port 8080. FastAPI docs available at `/docs`.

## Key Patterns
- **Database access:** Always use `async with get_db() as db:` or the `@with_db` decorator
- **Caching:** `storage_cache.py` CacheManager — check cache before querying DB for events/venues/persons
- **Auth flow:** AuthMiddleware silently refreshes expired access tokens using refresh token cookie
- **Payments:** Create a `Payment` record first, then a `PaymentIntent`, then redirect to provider
- **UI pages:** Each page file registers its own NiceGUI routes via `@ui.page()`
- **Admin pages:** Under `pages/admin_pages/` — restricted to `PersonStatus.member` or higher

## Timezone
All event times use `Asia/Yerevan` timezone.

## Deployment
- Docker image: `python:3.13-slim`, port 8080, `CMD python main.py`
- CI/CD: `cloudbuild.yaml` — Google Cloud Build with Telegram notifications on deploy
- Secrets: injected via Cloud Build secret manager (not in source)
