# A serializer turns model objects (Python) into JSON (text for the API).

from rest_framework import serializers
from .models import FlightOffer, Route


# A route as JSON:  {"origin": "BSZ", "destination": "TYO"}
class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["origin", "destination"]


# A flight offer as JSON
class FlightOfferSerializer(serializers.ModelSerializer):
    # Nested serializer: show the whole route, not only its id
    #   without:  "route": 1
    #   with:     "route": {"origin": "BSZ", "destination": "TYO"}
    route = RouteSerializer()

    class Meta:

        model = FlightOffer
        fields = [
            "id",
            "route",
            "departure_at",
            "price",
            "airline",
            "transfers",
            "duration",
            "link",
            "found_at",
        ]
