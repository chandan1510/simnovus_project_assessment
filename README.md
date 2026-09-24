# Mini Device Fleet Monitor

A small Django app that tracks heartbeats from simulated devices and reports which are ONLINE/OFFLINE.

## Design
- `monitor/models.py` – one `Device` model (SQLite). Stores the device's own heartbeat timestamp, plus the **server receive time** (`last_seen`).
- **Timeout rule:** status is *computed on every read*: `ONLINE` if `last_seen` is within 30s of now, else `OFFLINE`. No background job, so it can never be stale.
- `monitor/views.py` – plain Django JSON views (no DRF, to keep it small).
- `simulator/simulate.py` – stdlib-only script that runs devices in threads.

## Prerequisites
Python 3.10+ and `pip`.

## Build / Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

## Run
```bash
python manage.py runserver          # http://127.0.0.1:8000
```
Optional: `HEARTBEAT_TIMEOUT=30` (seconds) env var.

## Run the simulator (second terminal)
```bash
python simulator/simulate.py                                   # 5 devices, heartbeat every 5s
python simulator/simulate.py --stop device-03 --stop-after 10  # device-03 goes silent after 10s
```
Then run `curl localhost:8000/summary` – about 30s after device-03 stops, it turns OFFLINE.

## Tests
```bash
python manage.py test
```

## Example requests
```bash
curl -X POST localhost:8000/devices -H 'Content-Type: application/json' \
     -d '{"id":"device-01","name":"Lab Device 01"}'
curl -X POST localhost:8000/devices/device-01/heartbeat -H 'Content-Type: application/json' \
     -d '{"timestamp":"2026-09-21T10:30:00Z","status":"OK","cpu_usage":42}'
curl localhost:8000/devices
curl "localhost:8000/devices?status=offline"
curl localhost:8000/devices/device-01
curl localhost:8000/summary
```
Errors return `{"error": "..."}` with 400 (bad input), 404 (unknown device) or 409 (duplicate id).

## Assumptions
- Status uses the **server's** receive time, not the device's `timestamp`, so a device with a wrong clock cannot appear ONLINE/OFFLINE incorrectly. The device timestamp is still stored and returned as `last_heartbeat`.
- A device that has never sent a heartbeat is OFFLINE.
- Extra heartbeat fields (e.g. `cpu_usage`) are stored as `metrics`.
- No authentication (out of scope).

## Known limitations
- SQLite and Django's dev server only; not for production.
- Only the latest heartbeat is kept (no history).
- No auth: anyone can register devices or send heartbeats.
- `?status=` filter is applied in Python after loading devices, which is fine for small fleets.

## With one more day
- Store heartbeat history and add a small dashboard.
- Per-device API tokens, Postgres, Docker, pagination, structured logging.
- Make `?status=` a DB query.

## AI Usage
- **Tools:** Claude, used to scaffold the Django project, views, tests and simulator.
- **Changed:** <FILL IN – e.g. the first draft judged status by the device-supplied timestamp; I changed it to server receive time to avoid clock-skew problems.>
- **Verified myself:** <FILL IN – e.g. ran the simulator, stopped device-03 and confirmed it turned OFFLINE after ~30s; ran the tests.>
