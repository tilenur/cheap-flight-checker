from django.urls import path
from .views import FlightOfferListView

# URLs of the flights app. They all start with /api/ (see config/urls.py).
#
#   "flights/"  →  /api/flights/
#
# .as_view() turns the view class into something the URL can call.
urlpatterns = [path("flights/", FlightOfferListView.as_view())]
