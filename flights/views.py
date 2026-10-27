from rest_framework.generics import ListAPIView
from .serializers import FlightOfferSerializer
from .models import FlightOffer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils import timezone


# Create your views here.
@method_decorator(cache_page(60 * 60), name="get")
class FlightOfferListView(ListAPIView):
    serializer_class = FlightOfferSerializer
    # queryset = FlightOffer.objects.all()

    def get_queryset(self):
        if FlightOffer.objects.exists():
            newest = FlightOffer.objects.latest("found_at")
            return FlightOffer.objects.filter(
                found_at__date=timezone.localtime(newest.found_at).date()
            ).order_by("price")
        else:
            return FlightOffer.objects.none()
