import os
import requests
from .models import FlightOffer

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
