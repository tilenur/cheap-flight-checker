from django.db import models


# Create your models here.
class Route(models.Model):
    origin = models.CharField(max_length=3)
    destination = models.CharField(max_length=3)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.origin} - {self.destination}"


class FlightOffer(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    departure_at = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    airline = models.CharField(max_length=3)
    transfers = models.PositiveSmallIntegerField()
    duration = models.PositiveSmallIntegerField()
    link = models.TextField()
    found_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.route} {self.departure_at} ${self.price}"
