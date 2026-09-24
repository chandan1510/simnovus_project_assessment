from django.urls import path
from . import views

urlpatterns = [
    path("devices", views.devices),
    path("devices/<str:device_id>", views.device_detail),
    path("devices/<str:device_id>/heartbeat", views.heartbeat),
    path("summary", views.summary),
]
