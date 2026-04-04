from django.urls import path
from .api_views import RouteAPIList, RouteAPIDetail

app_name = 'routes-api'

urlpatterns = [
    path('', RouteAPIList.as_view(), name='list'),
    path('<int:pk>/', RouteAPIDetail.as_view(), name='detail'),
]
