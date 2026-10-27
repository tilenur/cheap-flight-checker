from django.db import models


# Create your models here.
#
# A model = a table in the database. Each field = a column.
# After changing a model, run:  makemigrations → migrate


# One direction to check, for example BSZ → TYO.
# The rows were added in the admin: BSZ-TYO and TYO-BSZ.
class Route(models.Model):
    origin = models.CharField(max_length=3)       # 3-letter code, e.g. BSZ
    destination = models.CharField(max_length=3)  # 3-letter code, e.g. TYO
    is_active = models.BooleanField(default=True)  # False = skip this route

    # How a route looks as text: "BSZ - TYO"
    def __str__(self):
        return f"{self.origin} - {self.destination}"


# One saved flight (one of the 3 cheapest of a month).
class FlightOffer(models.Model):
    # Which route it belongs to.
    # CASCADE = if the route is deleted, its offers are deleted too.
    route = models.ForeignKey(Route, on_delete=models.CASCADE)

    departure_at = models.DateTimeField()  # when the plane takes off (UTC)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # in USD
    airline = models.CharField(max_length=3)  # e.g. CZ, CA
    transfers = models.PositiveSmallIntegerField()  # 0 = direct, 1 = one stop
    duration = models.PositiveSmallIntegerField()  # flight time in minutes
    link = models.TextField()  # Aviasales link (very long, so TextField)

    # When WE saved it. auto_now_add = Django fills it in automatically.
    found_at = models.DateTimeField(auto_now_add=True)

    # How an offer looks as text: "BSZ - TYO 2026-11-22 17:20:00+00:00 $405.00"
    def __str__(self):
        return f"{self.route} {self.departure_at} ${self.price}"
