"""Runtime settings, read from the environment."""
import os
from zoneinfo import ZoneInfo

DATABASE_PATH = os.environ.get("RIDER_DB_PATH", "rider.db")
# Timezone that defines the shuttle "service day" (what "today" means).
SERVICE_TZ = ZoneInfo(os.environ.get("SERVICE_TZ", "UTC"))
# How many days of departures the seed materialises, starting today.
SEED_DAYS = int(os.environ.get("SEED_DAYS", "7"))
