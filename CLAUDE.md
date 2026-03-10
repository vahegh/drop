# DROP Dead Disco - CLAUDE.md

## Project Overview
Full-stack event management and ticketing platform for a nightclub venue in Yerevan, Armenia.
Production: https://dropdeadisco.com - deployed on Google Cloud Run.

## Tech Stack
- **UI:** React + TypeScript (Vite 7, React Router v6, TanStack Query, shadcn/ui, Tailwind v4)
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
main.py               # Entry point - FastAPI server, middleware, route registration, serves React build
db.py                 # Async PostgreSQL engine (pool 10+5, 3600s recycle)
db_models.py          # SQLAlchemy ORM models
api_models.py         # Pydantic request/response models
enums.py              # PersonStatus, PaymentStatus, PaymentProvider
consts.py             # Email addresses, templates, regexes, URLs
dependencies.py       # AuthMiddleware (cookie-based auth, request.state injection)
storage_cache.py      # In-memory cache, 120-min TTL
helpers.py            # Utility functions (user agent, analytics)
decorators.py         # @with_db decorator, verify_user_token

frontend/             # React + TypeScript frontend (Vite)
  src/pages/          # React page components (Home, Event, BuyTicket, Profile, Login, etc.)
  src/api/            # Axios functions per domain
  src/hooks/          # TanStack Query hooks (useMe, useEvents, useTickets, etc.)
  src/types/          # TypeScript mirrors of api_models.py

routes/               # FastAPI endpoints (auth, attendance, apple_pass_updates, event, telegram_webhook)
routes/client/        # REST API for React frontend - all prefixed /api/client/
services/             # Business logic (25+ modules)
migrations/           # Alembic schema versions (50+)
templates/            # Jinja2 HTML email templates
static/               # Images, bg_video.mp4, favicon
apple-pass-images/    # Apple Wallet pass assets
```

## Database Models
- `Venue` - event locations
- `Person` - users (status: pending/verified/rejected/member)
- `Event` - events with pricing tiers (early_bird, general_admission, member)
- `MemberPass` - one per person, links to Apple/Google pass URLs
- `EventTicket` - one per (person, event), tracks attended_at
- `Payment` - orders (BigInteger order_id, multi-provider)
- `PaymentIntent` - async payment tracking
- `RefreshToken` - JWT refresh tokens
- `CardBinding` - stored card data for 1-click payments
- `Drink` / `DrinkVoucher` / `DrinkPaymentIntent` - drink voucher system
- `AppleDevices` / `AppleDeviceRegistrations` - Apple Wallet push tracking

All PKs are UUIDs (`gen_random_uuid()`). No hard deletes - status changes only.

## Environment Variables
- `db_conn_string` - PostgreSQL async connection string (required at startup)
- `env` - set to `"local"` to enable GA4 debug mode and suppress Meta Pixel

## Running Locally
```bash
# Backend (requires .env file with db_conn_string)
python main.py
# App starts on port 8080. FastAPI docs at /docs.

# React dev server (proxies /api and /static to :8080)
cd frontend && npm run dev
# Vite dev server at localhost:5173
```
In production, Python serves the built React app from `frontend/dist/`.

## Workflow
- **After every code change, stage and commit it immediately.** No exceptions.

## Key Patterns
- **Database access:** Always use `async with get_db() as db:` or the `@with_db` decorator
- **Caching:** `storage_cache.py` CacheManager - check cache before querying DB for events/venues/persons
- **Auth flow:** AuthMiddleware silently refreshes expired access tokens using refresh token cookie
- **Payments:** Create a `Payment` record first, then a `PaymentIntent`, then redirect to provider
- **REST API:** All client endpoints in `routes/client/`, prefixed `/api/client/`; auth via `verify_user_token(request)` from `decorators.py`
- **UI pages:** React pages under `frontend/src/pages/`; routing via React Router v6
- **Analytics:** `window.__ENV__` injected by Python at startup; GA4 debug mode when `env=local`, Meta Pixel suppressed when `env=local`

## Timezone
All event times use `Asia/Yerevan` timezone.

## Deployment
- Docker image: multi-stage build - Node 22 builds React (`frontend/dist/`), then `python:3.13-slim` copies the dist and runs `python main.py` on port 8080
- CI/CD: `cloudbuild.yaml` - Google Cloud Build with Telegram notifications on deploy
- Secrets: injected via Cloud Build secret manager (not in source)
