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
    from_city = serializers.SerializerMethodField()
    to_city = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    def get_from_city(self, obj):
        first = obj.stops.order_by('order').first()
        return first.city if first else ''

    def get_to_city(self, obj):
        last = obj.stops.order_by('order').last()
        return last.city if last else ''

    def get_price(self, obj):
        first = obj.stops.order_by('order').first()
        last = obj.stops.order_by('order').last()
        if not first or not last:
            return 0
        return max(0, float(last.price_from_start) - float(first.price_from_start))

    class Meta:
        model = Route
        fields = (
            'id', 'from_city', 'to_city', 'departure_time',
            'price', 'transport', 'transport_id', 'is_approved',
        )
        read_only_fields = ('is_approved',)
