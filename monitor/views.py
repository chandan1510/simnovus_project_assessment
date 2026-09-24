import json

from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Device, cutoff


def error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def json_body(request):
    """Parsed JSON object, or None if the body is not a JSON object."""
    try:
        data = json.loads(request.body)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


@csrf_exempt  # JSON API for devices, no browser sessions
@require_http_methods(["GET", "POST"])
def devices(request):
    if request.method == "GET":
        items = [d.to_dict() for d in Device.objects.order_by("id")]
        wanted = request.GET.get("status", "").upper()
        if wanted:
            items = [d for d in items if d["status"] == wanted]
        return JsonResponse(items, safe=False)

    data = json_body(request)
    if data is None:
        return error("Body must be a JSON object")
    device_id, name = data.get("id"), data.get("name")
    if not (isinstance(device_id, str) and device_id.strip() and isinstance(name, str) and name.strip()):
        return error("'id' and 'name' must be non-empty strings")
    if Device.objects.filter(pk=device_id).exists():
        return error("Device already registered", 409)
    device = Device.objects.create(id=device_id, name=name)
    return JsonResponse(device.to_dict(), status=201)


@require_GET
def device_detail(request, device_id):
    device = Device.objects.filter(pk=device_id).first()
    return JsonResponse(device.to_dict()) if device else error("Device not found", 404)


@csrf_exempt
@require_POST
def heartbeat(request, device_id):
    device = Device.objects.filter(pk=device_id).first()
    if not device:
        return error("Device not found", 404)
    data = json_body(request)
    if data is None:
        return error("Body must be a JSON object")

    ts = data.get("timestamp")
    parsed = parse_datetime(ts) if isinstance(ts, str) else None
    if parsed is None:
        return error("'timestamp' must be an ISO 8601 string")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.utc)
    status = data.get("status")
    if not (isinstance(status, str) and status):
        return error("'status' must be a non-empty string")

    device.last_heartbeat = parsed
    device.last_seen = timezone.now()
    device.reported_status = status
    device.metrics = {k: v for k, v in data.items() if k not in ("timestamp", "status")}
    device.save()
    return JsonResponse(device.to_dict())


@require_GET
def summary(request):
    total = Device.objects.count()
    online = Device.objects.filter(last_seen__gte=cutoff()).count()
    return JsonResponse({"total": total, "online": online, "offline": total - online})
