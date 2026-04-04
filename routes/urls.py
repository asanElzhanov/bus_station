from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
    # Public
    path('', views.RouteListView.as_view(), name='list'),
    path('<int:pk>/', views.RouteDetailView.as_view(), name='detail'),

    # Manager
    path('manage/', views.ManagerRouteListView.as_view(), name='manager_list'),
    path('create/', views.RouteCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.RouteEditView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.RouteDeleteView.as_view(), name='delete'),

    # Admin
    path('<int:pk>/approve/', views.RouteApproveView.as_view(), name='approve'),
    path('<int:pk>/reject/', views.RouteRejectView.as_view(), name='reject'),
]
