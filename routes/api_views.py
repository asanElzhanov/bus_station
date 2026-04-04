from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from .models import Route
from .serializers import RouteSerializer


class RouteAPIList(APIView):
    """GET /api/routes/ — public list of approved routes."""
    permission_classes = [AllowAny]

    def get(self, request):
        routes = Route.objects.filter(is_approved=True).select_related('transport')
        serializer = RouteSerializer(routes, many=True)
        return Response(serializer.data)


class RouteAPIDetail(APIView):
    """GET /api/routes/<pk>/ — single route details."""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        route = get_object_or_404(Route, pk=pk, is_approved=True)
        serializer = RouteSerializer(route)
        return Response(serializer.data)
