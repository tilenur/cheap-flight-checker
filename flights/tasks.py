# Celery tasks = functions the Celery worker runs in the background.
# Celery finds this file by itself (autodiscover_tasks in config/celery.py).

from celery import shared_task
from .services import fetch_all_prices, build_message, post_telegram


# The morning routine. Beat runs it every day at 9:00.
#
# To run it by hand (in python manage.py shell):
#   fetch_flights_task.delay()
@shared_task
def fetch_flights_task():
    # 1. Get the prices, save them, clear the cache
    fetch_all_prices()

    # 2. Send the Telegram message.
    #    (It's here and not in fetch_all_prices, so the fetch_flights
    #    command doesn't send a message every time we test.)
    post_telegram(build_message())
