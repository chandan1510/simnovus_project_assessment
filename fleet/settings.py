import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-key")
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = ["monitor"]
ROOT_URLCONF = "fleet.urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
USE_TZ = True
TIME_ZONE = "UTC"

# Seconds without a heartbeat before a device is OFFLINE.
HEARTBEAT_TIMEOUT = int(os.environ.get("HEARTBEAT_TIMEOUT", 30))
