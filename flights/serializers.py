from rest_framework import serializers
from .models import FlightOffer, Route


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["origin", "destination"]


class FlightOfferSerializer(serializers.ModelSerializer):
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
