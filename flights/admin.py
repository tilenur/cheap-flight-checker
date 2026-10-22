from django.contrib import admin
from .models import Route, FlightOffer

# Register your models here.
admin.site.register(Route)


@admin.register(FlightOffer)
class FlightOfferAdmin(admin.ModelAdmin):
    list_display = ["route", "departure_at", "price", "airline", "transfers"]
