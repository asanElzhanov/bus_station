from rest_framework import serializers
from .models import Route
from transport.models import Transport


class TransportShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transport
        fields = ('id', 'name', 'total_seats')


class RouteSerializer(serializers.ModelSerializer):
    transport = TransportShortSerializer(read_only=True)
    transport_id = serializers.PrimaryKeyRelatedField(
        queryset=Transport.objects.all(), source='transport', write_only=True
    )

    class Meta:
        model = Route
        fields = (
            'id', 'from_city', 'to_city', 'departure_time',
            'price', 'transport', 'transport_id', 'is_approved',
        )
        read_only_fields = ('is_approved',)
