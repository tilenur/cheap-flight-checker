import os
import requests
from .models import FlightOffer, Route
from datetime import date
from django.core.cache import cache

API_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"


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
