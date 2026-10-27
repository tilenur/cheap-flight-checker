from django.core.management.base import BaseCommand
from flights.models import Route
from datetime import date
from flights.services import save_prices


class Command(BaseCommand):
    help = "Fetch cheapest flight prices and save them"

    def handle(self, *args, **options):

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
                self.stdout.write(f"{active_route} {month}")
                save_prices(active_route, month)
