"""Simulate devices sending heartbeats. Uses only the standard library.

  python simulator/simulate.py                          # 5 devices, every 5s
  python simulator/simulate.py --stop device-03 --stop-after 10   # device-03 goes silent after 10s
"""
import argparse
import json
import random
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


def call(base, path, payload):
    req = urllib.request.Request(
        base + path, json.dumps(payload).encode(), {"Content-Type": "application/json"}
    )
    try:
        return urllib.request.urlopen(req).status
    except urllib.error.HTTPError as e:
        return e.code


def run_device(base, device_id, interval, stop_at, halt):
    call(base, "/devices", {"id": device_id, "name": f"Sim {device_id}"})  # 409 if it already exists
    while not halt.is_set() and time.time() < stop_at:
        code = call(base, f"/devices/{device_id}/heartbeat", {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "OK",
            "cpu_usage": random.randint(10, 90),
            "signal_strength": random.randint(-90, -50),
        })
        print(f"{device_id} -> heartbeat ({code})")
        halt.wait(interval)
    print(f"{device_id} stopped")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8000")
    p.add_argument("--devices", type=int, default=5)
    p.add_argument("--interval", type=float, default=5)
    p.add_argument("--stop", help="device id to silence, e.g. device-03")
    p.add_argument("--stop-after", type=float, default=15, help="seconds before --stop device goes silent")
    a = p.parse_args()

    halt, now = threading.Event(), time.time()
    threads = []
    for i in range(1, a.devices + 1):
        did = f"device-{i:02d}"
        stop_at = now + a.stop_after if did == a.stop else float("inf")
        t = threading.Thread(target=run_device, args=(a.url, did, a.interval, stop_at, halt), daemon=True)
        t.start()
        threads.append(t)
    try:
        while any(t.is_alive() for t in threads):
            time.sleep(0.5)
    except KeyboardInterrupt:
        halt.set()


if __name__ == "__main__":
    main()
