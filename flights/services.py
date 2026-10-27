import os
import requests

from .models import FlightOffer, Route
from datetime import date
from django.core.cache import cache
from django.utils import timezone
from zoneinfo import ZoneInfo

API_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

AIRPORT_ZONES = {
    "BSZ": ZoneInfo("Asia/Bishkek"),
    "TYO": ZoneInfo("Asia/Tokyo"),
}


def get_prices(origin, destination, month):
    token = os.environ.get("TRAVELPAYOUTS_TOKEN")

    response = requests.get(
        API_URL,
        params={
            "origin": origin,
            "destination": destination,
            "departure_at": month,
            "one_way": "true",
            "currency": "usd",
            "sorting": "price",
            "token": token,
        },
        timeout=20,
    )
    response.raise_for_status()

    result = response.json()
    return result["data"]


def save_prices(route, month):
    flights = get_prices(route.origin, route.destination, month)
    good_flights = [f for f in flights if f["transfers"] < 2]
    three_first_flights = good_flights[:3]

    for t in three_first_flights:
        FlightOffer.objects.create(
            route=route,
            departure_at=t["departure_at"],
            price=t["price"],
            airline=t["airline"],
            transfers=t["transfers"],
            duration=t["duration"],
            link="https://www.aviasales.com" + t["link"],
        )


def fetch_all_prices():
    today = date.today()
    months = []
    for i in range(1, 4):
        m = today.month + i
        y = today.year
        if m > 12:
            m = m - 12
            y = y + 1
        months.append(f"{y:02d}-{m:02d}")

    active_routes = Route.objects.filter(is_active=True)

    for active_route in active_routes:
        for month in months:
            print(f"{active_route} {month}")
            save_prices(active_route, month)

    cache.clear()


def post_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        },
        timeout=20,
    )
    response.raise_for_status()


def build_message():
    newest = FlightOffer.objects.latest("found_at")
    day = timezone.localtime(newest.found_at).date()
    active_routes = Route.objects.filter(is_active=True)

    lines = [f"✈️ Cheapest flights ({day.strftime('%b %d')})", ""]

    for active_route in active_routes:
        offers = FlightOffer.objects.filter(
            route=active_route, found_at__date=day
        ).order_by("departure_at")

        route_lines = [
            f"<b>{active_route.origin} → {active_route.destination}</b>"
        ]
        month = None
        zone = AIRPORT_ZONES[active_route.origin]

        for offer in offers:
            departure = timezone.localtime(offer.departure_at, zone)
            if month is not None and departure.month != month:
                route_lines.append("")
            month = departure.month

            if offer.transfers == 0:
                status = "direct"
            else:
                status = "1 stop"
            route_lines.append(
                f"{departure.strftime("%b %d")} ${offer.price:.0f} {offer.airline} {status} <a href='{offer.link.split("?")[0]}'>Book</a>"
            )
        lines.append("<blockquote>" + "\n".join(route_lines) + "</blockquote>")

    return "\n".join(lines)
