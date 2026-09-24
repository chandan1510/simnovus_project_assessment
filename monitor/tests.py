import json
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

HB = {"timestamp": "2026-09-21T10:30:00Z", "status": "OK"}


class FleetTests(TestCase):
    def post(self, url, data):
        return self.client.post(url, json.dumps(data), content_type="application/json")

    def register(self, id="d1", name="Device 1"):
        return self.post("/devices", {"id": id, "name": name})

    # --- registration ---
    def test_register_device(self):
        r = self.register()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["status"], "OFFLINE")  # no heartbeat yet

    def test_register_duplicate_and_invalid(self):
        self.register()
        self.assertEqual(self.register().status_code, 409)
        self.assertEqual(self.post("/devices", {"id": "x"}).status_code, 400)
        r = self.client.post("/devices", "not json", content_type="application/json")
        self.assertEqual(r.status_code, 400)

    # --- heartbeat ---
    def test_heartbeat_updates_device(self):
        self.register()
        r = self.post("/devices/d1/heartbeat", {**HB, "cpu_usage": 42})
        self.assertEqual(r.status_code, 200)
        d = self.client.get("/devices/d1").json()
        self.assertEqual(d["status"], "ONLINE")
        self.assertEqual(d["last_heartbeat"], "2026-09-21T10:30:00+00:00")
        self.assertEqual(d["metrics"], {"cpu_usage": 42})

    def test_heartbeat_errors(self):
        self.assertEqual(self.post("/devices/nope/heartbeat", HB).status_code, 404)
        self.register()
        self.assertEqual(self.post("/devices/d1/heartbeat", {"status": "OK"}).status_code, 400)
        self.assertEqual(self.post("/devices/d1/heartbeat", {**HB, "timestamp": "bad"}).status_code, 400)

    # --- 30 second rule ---
    def test_online_then_offline_after_timeout(self):
        self.register()
        start = timezone.now()
        self.post("/devices/d1/heartbeat", HB)
        for delta, expected in [(29, "ONLINE"), (31, "OFFLINE")]:
            with patch("django.utils.timezone.now", return_value=start + timedelta(seconds=delta)):
                self.assertEqual(self.client.get("/devices/d1").json()["status"], expected)

    def test_new_heartbeat_brings_device_back_online(self):
        self.register()
        start = timezone.now()
        self.post("/devices/d1/heartbeat", HB)
        later = start + timedelta(seconds=60)
        with patch("django.utils.timezone.now", return_value=later):
            self.assertEqual(self.client.get("/devices/d1").json()["status"], "OFFLINE")
            self.post("/devices/d1/heartbeat", HB)
            self.assertEqual(self.client.get("/devices/d1").json()["status"], "ONLINE")

    # --- list / summary ---
    def test_list_filter_and_summary(self):
        for i in ("d1", "d2", "d3"):
            self.register(i)
        self.post("/devices/d1/heartbeat", HB)
        self.post("/devices/d2/heartbeat", HB)
        self.assertEqual(self.client.get("/summary").json(), {"total": 3, "online": 2, "offline": 1})
        self.assertEqual(len(self.client.get("/devices").json()), 3)
        online = self.client.get("/devices?status=online").json()
        self.assertEqual([d["id"] for d in online], ["d1", "d2"])
        with patch("django.utils.timezone.now", return_value=timezone.now() + timedelta(seconds=45)):
            self.assertEqual(self.client.get("/summary").json(), {"total": 3, "online": 0, "offline": 3})

    def test_unknown_device_404(self):
        self.assertEqual(self.client.get("/devices/nope").status_code, 404)
