from django.contrib import admin
from .models import Route, FlightOffer

# Register your models here.
#
# "Register" = show the model on the admin page (/admin/),
# so we can see, add, change and delete rows there.


# Simple way: the default look
admin.site.register(Route)


# Decorator way: with our own settings
@admin.register(FlightOffer)
class FlightOfferAdmin(admin.ModelAdmin):
    # Columns shown in the list of offers
    list_display = ["route", "departure_at", "price", "airline", "transfers"]
