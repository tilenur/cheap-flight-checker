from django.core.management.base import BaseCommand
from flights.models import Route
from datetime import date


class Command(BaseCommand):
    help = "Fetch cheapest flight prices and save them"

    def handle(self, *args, **options):
        active_routes = Route.objects.filter(is_active=True)

        for active_route in active_routes:
            self.stdout.write(str(active_route))

        today = date.today()
        months = []
        for i in range(1, 4):
            m = today.month + i
            y = today.year
            if m > 12:
                m = m - 12
                y = y + 1
            months.append(f"{y:02d}-{m:02d}")
        self.stdout.write(str(months))
