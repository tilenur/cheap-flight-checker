# Our own manage.py command. The file name is the command name:
#
#   python manage.py fetch_flights
#
# (The folders management/ and commands/ each need an __init__.py file.)

from django.core.management.base import BaseCommand
from flights.services import fetch_all_prices


# Django looks for a class named exactly "Command"
class Command(BaseCommand):
    # Shown with: python manage.py help fetch_flights
    help = "Fetch cheapest flight prices and save them"

    # Runs when you call the command.
    #   *args     = extra values without names
    #   **options = extra values with names
    # We don't use them, but Django passes them, so we must accept them.
    def handle(self, *args, **options):
        # The real work is in services.py (shared with the Celery task).
        # No Telegram message here.
        fetch_all_prices()
