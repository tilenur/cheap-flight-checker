from celery import shared_task
from .services import fetch_all_prices


@shared_task
def fetch_flights_task():
    fetch_all_prices()
