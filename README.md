# ✈️ Cheap Flight Checker

A Django backend that checks flight prices between **Bishkek (BSZ)** and **Tokyo (TYO)** every morning and sends the cheapest options to Telegram.

Every day at **9:00 (Bishkek time)** it:

1. asks the Travelpayouts (Aviasales) API for one-way flights in both directions, for the next 3 months;
2. keeps the **3 cheapest flights per month** with **max 1 stop**, and saves them to PostgreSQL;
3. clears the API cache;
4. sends a formatted message to Telegram.

The newest offers are also available as JSON at `/api/flights/`, cached in Redis.

```
✈️ Cheapest flights (Oct 28)

┃ BSZ → TYO
┃ Nov 22 $405 CZ 1 stop Book
┃ Nov 24 $415 CZ 1 stop Book
┃
┃ Dec 08 $401 CZ 1 stop Book
┃ ...

┃ TYO → BSZ
┃ Nov 05 $432 CA 1 stop Book
┃ ...
```

## Tech stack

| Tool | Used for |
|---|---|
| Python 3.14, Django 6.1 | models, admin, settings, management command |
| Django REST Framework | the `/api/flights/` endpoint |
| PostgreSQL 17 | routes and flight offers |
| Redis 7 | Celery broker (db 0) and API cache (db 1) |
| Celery + Celery Beat | the daily 9:00 background task |
| Docker Compose | runs PostgreSQL and Redis |
| Travelpayouts Data API v3 | flight prices (`prices_for_dates`) |
| Telegram Bot API | the daily message |

## How it works

```
Celery Beat (9:00) ──► Redis (broker) ──► Celery worker: fetch_flights_task()
                                              │
                                              ├─ fetch_all_prices()
                                              │    ├─ delete today's offers (safe re-runs)
                                              │    ├─ Travelpayouts API: 2 routes × 3 months
                                              │    ├─ save the 3 cheapest per month (max 1 stop)
                                              │    └─ clear the Redis cache
                                              └─ post_telegram(build_message())

Browser ──► /api/flights/ ──► Redis cache (1 hour) or PostgreSQL ──► JSON
```

All the real work is in `flights/services.py`. The Celery task and the `fetch_flights` management command both call it, so the logic is written once.

## Project structure

```
config/
  settings.py        database, Celery, Beat schedule, cache, timezone
  celery.py          the Celery app
  urls.py            admin/ and api/
flights/
  models.py          Route, FlightOffer
  services.py        API calls, saving, Telegram message
  tasks.py           the Celery task
  serializers.py     FlightOffer → JSON
  views.py           the API view (cached)
  management/commands/fetch_flights.py
docker-compose.yml   PostgreSQL + Redis
docs/                study notes (PDF)
```

## Setup

**1. Install**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Create a `.env` file** in the project folder:

```
POSTGRES_DB=flights
POSTGRES_USER=flights_user
POSTGRES_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5434

TRAVELPAYOUTS_TOKEN=your-travelpayouts-token
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

- Travelpayouts token: from your account at [travelpayouts.com](https://www.travelpayouts.com).
- Telegram bot token: create a bot with [@BotFather](https://t.me/BotFather).
- Chat ID: send your bot a message, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` and find `"chat": {"id": ...}`.

**3. Start the database and Redis**

```bash
docker compose up -d
```

**4. Create the tables and an admin user**

```bash
python manage.py migrate
python manage.py createsuperuser
```

**5. Add routes** in the admin (`/admin/`): `BSZ → TYO` and `TYO → BSZ`, both active.
Note: Travelpayouts uses **BSZ** for Bishkek, not FRU.

## Running

Use three terminals (with `.venv` activated in each):

```bash
python manage.py runserver                              # the API
celery -A config worker --pool=solo --loglevel=info     # runs the tasks
celery -A config beat --loglevel=info                   # starts the task at 9:00
```

`--pool=solo` is needed on macOS with Python 3.14. Restart the worker after changing code.

Run things by hand:

```bash
python manage.py fetch_flights          # fetch and save prices (no Telegram)
```

```python
# python manage.py shell
from flights.tasks import fetch_flights_task
fetch_flights_task.delay()              # the full morning job, through Celery
```

## API

`GET /api/flights/`: the offers from the newest day, cheapest first.

```json
[
  {
    "id": 1,
    "route": {"origin": "BSZ", "destination": "TYO"},
    "departure_at": "2026-12-08T05:30:00+06:00",
    "price": "401.00",
    "airline": "CZ",
    "transfers": 1,
    "duration": 980,
    "link": "https://www.aviasales.com/search/...",
    "found_at": "2026-10-28T09:00:12+06:00"
  }
]
```

## Things I learned

- **The prices are not live.** Travelpayouts returns prices saved from other people's recent searches, so the website can show a different price. Months far ahead have fewer results.
- **Timezones:** the database stores UTC. "Which day" uses Bishkek time, and departure dates use the departure airport's time.
- **Safe re-runs:** running the job twice on the same day replaces that day's offers instead of adding duplicates.
- **Telegram limits:** full Aviasales links were too long (`ENTITIES_TOO_LONG`), so the link is cut to the page + ticket ID.
- **Secrets:** tokens live only in `.env`, and Telegram errors are re-raised without the URL, so the token never shows in logs.

## Ideas for later

- Tests (month logic, `build_message`, mocked API calls)
- Fetch everything first, then save inside `transaction.atomic()`
- Retries and a Telegram alert when the task fails
- Price-drop alerts and a price history
- Run Django and Celery in Docker, and deploy to a server
