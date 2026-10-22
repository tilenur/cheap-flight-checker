import os
import requests

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
