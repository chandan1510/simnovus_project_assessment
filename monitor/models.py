from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def cutoff():
    """Devices last seen before this moment are OFFLINE."""
    return timezone.now() - timedelta(seconds=settings.HEARTBEAT_TIMEOUT)


class Device(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=128)
    last_heartbeat = models.DateTimeField(null=True)  # timestamp sent by the device
    last_seen = models.DateTimeField(null=True)       # server receive time (drives status)
    reported_status = models.CharField(max_length=32, blank=True)
    metrics = models.JSONField(default=dict)

    @property
    def status(self):
        # Computed on read, so no background job is needed.
        return "ONLINE" if self.last_seen and self.last_seen >= cutoff() else "OFFLINE"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "reported_status": self.reported_status,
            "metrics": self.metrics,
        }
