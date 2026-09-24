from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(url="/devices", permanent=False)),
    path("devices", views.devices),
    path("devices/<str:device_id>", views.device_detail),
    path("devices/<str:device_id>/heartbeat", views.heartbeat),
    path("summary", views.summary),
]
