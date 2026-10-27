from celery import shared_task
from .services import fetch_all_prices, build_message, post_telegram


@shared_task
def fetch_flights_task():
    fetch_all_prices()
    post_telegram(build_message())
