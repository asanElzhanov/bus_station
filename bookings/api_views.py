"""
API: возвращает занятые seat_id для конкретного сегмента маршрута и даты.
GET /api/bookings/seats/<route_pk>/<from_stop_pk>/<to_stop_pk>/<travel_date>/
"""

from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from routes.models import Route, Stop
from .views import get_occupied_seat_ids


class BookingSeatStatusAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, route_pk, from_stop_pk, to_stop_pk, travel_date):
        route     = get_object_or_404(Route, pk=route_pk, is_approved=True)
        from_stop = get_object_or_404(Stop, pk=from_stop_pk, route=route)
        to_stop   = get_object_or_404(Stop, pk=to_stop_pk, route=route)

        if from_stop.order >= to_stop.order:
            return Response({'error': 'from_stop должен быть раньше to_stop'}, status=400)

        try:
            date_obj = date.fromisoformat(travel_date)
        except ValueError:
            return Response({'error': 'Формат даты: YYYY-MM-DD'}, status=400)

        occupied = list(get_occupied_seat_ids(route, date_obj, from_stop, to_stop))
        price    = route.segment_price(from_stop, to_stop)

        return Response({
            'occupied_seat_ids': occupied,
            'segment': f'{from_stop.city} → {to_stop.city}',
            'price': price,
            'date': travel_date,
        })
