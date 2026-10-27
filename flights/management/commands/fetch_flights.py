from django.core.management.base import BaseCommand
from flights.services import fetch_all_prices


class Command(BaseCommand):
    help = "Fetch cheapest flight prices and save them"

    def handle(self, *args, **options):
        fetch_all_prices()
