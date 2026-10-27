from django.urls import path
from .views import FlightOfferListView

urlpatterns = [path("flights/", FlightOfferListView.as_view())]
