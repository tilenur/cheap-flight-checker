from rest_framework.generics import ListAPIView
from .serializers import FlightOfferSerializer
from .models import FlightOffer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils import timezone


# Create your views here.


# The API page: /api/flights/
#
# Shows the offers from the newest day, cheapest first, as JSON.
#
# Cache:
#   The answer is saved in Redis (drawer 1) for 1 hour (60 * 60 seconds).
#   1st request  → PostgreSQL → the copy is saved in Redis
#   next ones    → the copy from Redis (faster)
#   The copy is also deleted after every fetch (cache.clear() in services.py).
#
#   cache_page        = the cache tool (made for functions)
#   method_decorator  = lets us use it on a class
#   name="get"        = put it on the get method (the browser sends GET)
@method_decorator(cache_page(60 * 60), name="get")
class FlightOfferListView(ListAPIView):
    # Which serializer turns the offers into JSON
    serializer_class = FlightOfferSerializer
    # queryset = FlightOffer.objects.all()

    # Decides WHICH offers the API shows
    def get_queryset(self):
        # Empty table → latest() would crash, so check first
        if FlightOffer.objects.exists():
            # The ONE newest offer
            newest = FlightOffer.objects.latest("found_at")

            # All offers found on the same day (Bishkek clock), cheapest first
            #   left:  found_at__date = the date part of every row
            #   right: localtime() = UTC → Bishkek, then .date()
            return FlightOffer.objects.filter(
                found_at__date=timezone.localtime(newest.found_at).date()
            ).order_by("price")
        else:
            # Empty QuerySet → the API shows []
            return FlightOffer.objects.none()
