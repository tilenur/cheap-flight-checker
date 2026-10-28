# The "work" of the project, in one place.
# Both the fetch_flights command and the Celery task use these functions.

import os
import requests

from .models import FlightOffer, Route
from datetime import date
from django.core.cache import cache
from django.utils import timezone
from zoneinfo import ZoneInfo

# Travelpayouts API: the cheapest tickets for a route and month
API_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

# Airport → its timezone
# (a ticket shows the local time of the airport where the plane takes off)
AIRPORT_ZONES = {
    "BSZ": ZoneInfo("Asia/Bishkek"),
    "TYO": ZoneInfo("Asia/Tokyo"),
}


# =============================================================================
# 1. Get and save prices
# =============================================================================


# Ask Travelpayouts for the flights of one route in one month.
# Returns a list of dicts, cheapest first.
def get_prices(origin, destination, month):
    # The secret token comes from .env
    token = os.environ.get("TRAVELPAYOUTS_TOKEN")

    response = requests.get(
        API_URL,
        # params = the "?key=value&..." part of the URL
        params={
            "origin": origin,
            "destination": destination,
            "departure_at": month,  # "2026-11" = the whole month
            "one_way": "true",
            "currency": "usd",
            "sorting": "price",  # cheapest first
            "token": token,
        },
        # Wait max 20 seconds, so the task never gets stuck
        timeout=20,
    )
    # Error answer (400, 401, 500...) → stop with an error
    response.raise_for_status()

    # JSON → Python dict. The flights are in "data".
    result = response.json()
    return result["data"]


# Save the 3 cheapest flights (max 1 stop) of one route + month.
def save_prices(route, month):
    flights = get_prices(route.origin, route.destination, month)

    # Keep only 0 or 1 stop, then take the first 3 (= the 3 cheapest)
    good_flights = [f for f in flights if f["transfers"] < 2]
    three_first_flights = good_flights[:3]

    # One new row in the FlightOffer table for each flight
    for t in three_first_flights:
        FlightOffer.objects.create(
            route=route,
            departure_at=t["departure_at"],
            price=t["price"],
            airline=t["airline"],
            transfers=t["transfers"],
            duration=t["duration"],
            # The API gives only the end of the link
            link="https://www.aviasales.com" + t["link"],
        )


# The main job: every active route × the next 3 months, then clear the cache.
def fetch_all_prices():
    # Today, on the Bishkek clock (e.g. Oct 28)
    now = timezone.localtime()
    today = now.date()

    # Run twice on the same day → replace today's offers, don't add more.
    # Only TODAY's rows are deleted. Older days stay (history).
    #   01:00 test  → Oct 28: 14 offers
    #   09:00 Beat  → delete those 14 → save 14 new → Oct 28: 14 offers
    FlightOffer.objects.filter(found_at__date=today).delete()

    # The next 3 months, starting from NEXT month
    # e.g. in October: ["2026-11", "2026-12", "2027-01"]
    months = []
    for i in range(1, 4):  # i = 1, 2, 3
        m = today.month + i
        y = today.year

        # After December: month 13 → January of next year
        if m > 12:
            m = m - 12
            y = y + 1

        months.append(f"{y:02d}-{m:02d}")  # :02d → 1 becomes "01"

    active_routes = Route.objects.filter(is_active=True)

    # 2 routes × 3 months = 6 API calls
    for active_route in active_routes:
        for month in months:
            print(f"{active_route} {month}")
            save_prices(active_route, month)

    # New prices are saved → delete the old API copy in Redis (drawer 1).
    # Runs once, after both loops.
    cache.clear()


# =============================================================================
# 2. Telegram
# =============================================================================


# Send a text to our Telegram chat through the bot.
def post_telegram(text):
    # token = which bot sends it, chat_id = who gets it (both in .env)
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",  # show <b>, <a>, <blockquote> nicely
            },
            timeout=20,
        )

    # No internet, timeout...
    # Our own short error. "from None" hides the original one,
    # because it shows the URL with the token.
    except requests.RequestException:
        raise RuntimeError("Telegram: could not connect") from None

    # Telegram said no (e.g. "text is too long").
    # Not raise_for_status(), because its error shows the token too.
    if not response.ok:
        raise RuntimeError(f"Telegram error: {response.json()["description"]}")


# Make the message text from the offers of the newest day.
#
#   ✈️ Cheapest flights (Oct 28)
#
#   ┃ BSZ → TYO
#   ┃ Nov 22 $405 CZ 1 stop Book
#   ┃
#   ┃ Dec 08 $401 CZ 1 stop Book
#
#   ┃ TYO → BSZ
#   ┃ ...
def build_message():
    # The newest day, on the Bishkek clock (same as in views.py)
    newest = FlightOffer.objects.latest("found_at")
    day = timezone.localtime(newest.found_at).date()
    active_routes = Route.objects.filter(is_active=True)

    # The BIG list = the whole message (title + empty line + boxes)
    lines = [f"✈️ Cheapest flights ({day.strftime('%b %d')})", ""]

    for active_route in active_routes:
        # This route's offers from that day, by date (Nov → Dec → Jan)
        offers = FlightOffer.objects.filter(
            route=active_route, found_at__date=day
        ).order_by("departure_at")

        # The SMALL list = one box, only for this route.
        # First line: the route name in bold.
        route_lines = [
            f"<b>{active_route.origin} → {active_route.destination}</b>"
        ]

        month = None  # the "sticky note": month of the previous offer
        zone = AIRPORT_ZONES[active_route.origin]  # departure airport's clock

        for offer in offers:
            # Same moment, on the departure airport's clock
            # (UTC from the database can show the day before)
            departure = timezone.localtime(offer.departure_at, zone)

            # Not the first offer + a new month → empty line
            if month is not None and departure.month != month:
                route_lines.append("")
            month = departure.month  # always remember the month

            if offer.transfers == 0:
                status = "direct"
            else:
                status = "1 stop"

            # e.g. "Nov 22 $405 CZ 1 stop Book"
            #   %b %d          → "Nov 22"
            #   :.0f           → no numbers after the dot
            #   split("&")[0]  → keep the page + "t=" (the ticket ID), cut the rest
            #
            #   full link:  .../search/BSZ0501TYO1?t=CZ1799...&search_date=...&expected_price=618
            #   our link:   .../search/BSZ0501TYO1?t=CZ1799...
            #   (the full link is too long: Telegram says ENTITIES_TOO_LONG)
            route_lines.append(
                f"{departure.strftime("%b %d")} ${offer.price:.0f} {offer.airline} {status} <a href='{offer.link.split("&")[0]}'>Book</a>"
            )

        # Glue this route's lines → put them in one box → add to the big list
        lines.append("<blockquote>" + "\n".join(route_lines) + "</blockquote>")

    # Glue the big list into one text
    return "\n".join(lines)
