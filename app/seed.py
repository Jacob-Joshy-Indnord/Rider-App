"""Fixed, idempotent seed data for routes, stops, shuttles and schedules.

Routes are not planned in-app (out of scope); this module is the single source
of the fixed network. Every insert is keyed on a natural unique key with
ON CONFLICT DO NOTHING, so re-applying the seed never creates duplicates.
"""
import datetime as dt
import sqlite3
from zoneinfo import ZoneInfo

from app import config

STOPS = [
    ("CAMPUS-A", "Campus A"),
    ("A-GATE", "Campus A North Gate"),
    ("CAMPUS-B", "Campus B"),
    ("B-PARK", "Campus B Park & Ride"),
    ("METRO", "Metro Station"),
]

# Outbound routes; the reverse direction is derived with the stops reversed.
OUTBOUND = [
    ("A-METRO", "METRO-A", "Campus A", ["CAMPUS-A", "A-GATE", "METRO"]),
    ("B-METRO", "METRO-B", "Campus B", ["CAMPUS-B", "B-PARK", "METRO"]),
]

SHUTTLES = [("SHUTTLE-1", 12), ("SHUTTLE-2", 12), ("SHUTTLE-3", 12), ("SHUTTLE-4", 12)]

# Daily timetable (local SERVICE_TZ time) per route, with the shuttle assigned.
TIMETABLE = {
    "A-METRO": ("SHUTTLE-1", ["07:30", "08:30", "16:00", "17:00"]),
    "METRO-A": ("SHUTTLE-1", ["08:00", "09:00", "16:30", "17:30"]),
    "B-METRO": ("SHUTTLE-2", ["07:45", "08:45", "16:15", "17:15"]),
    "METRO-B": ("SHUTTLE-2", ["08:15", "09:15", "16:45", "17:45"]),
}


def _route_defs():
    for out_code, back_code, campus, stops in OUTBOUND:
        yield out_code, f"{campus} → Metro", stops
        yield back_code, f"Metro → {campus}", list(reversed(stops))


def _ids(conn, table):
    return {r["code"]: r["id"] for r in conn.execute(f"SELECT id, code FROM {table}")}


def apply_seed(conn: sqlite3.Connection, start_date: dt.date | None = None,
               days: int | None = None, tz: ZoneInfo | None = None) -> None:
    """Upsert the fixed network and materialise departures for `days` days."""
    tz = tz or config.SERVICE_TZ
    days = config.SEED_DAYS if days is None else days
    start_date = start_date or dt.datetime.now(tz).date()

    conn.execute("BEGIN")
    try:
        conn.executemany(
            "INSERT INTO stops (code, name) VALUES (?, ?) ON CONFLICT (code) DO NOTHING", STOPS)
        stop_ids = _ids(conn, "stops")

        for code, name, stops in _route_defs():
            conn.execute(
                "INSERT INTO routes (code, name, origin_stop_id, destination_stop_id) "
                "VALUES (?, ?, ?, ?) ON CONFLICT (code) DO NOTHING",
                (code, name, stop_ids[stops[0]], stop_ids[stops[-1]]))
        route_ids = _ids(conn, "routes")

        for code, _, stops in _route_defs():
            conn.executemany(
                "INSERT INTO route_stops (route_id, stop_id, position) VALUES (?, ?, ?) "
                "ON CONFLICT DO NOTHING",
                [(route_ids[code], stop_ids[s], pos) for pos, s in enumerate(stops, start=1)])

        conn.executemany(
            "INSERT INTO shuttles (code, seat_count) VALUES (?, ?) ON CONFLICT (code) DO NOTHING",
            SHUTTLES)
        shuttles = {r["code"]: (r["id"], r["seat_count"])
                    for r in conn.execute("SELECT id, code, seat_count FROM shuttles")}

        rows = []
        for offset in range(days):
            day = start_date + dt.timedelta(days=offset)
            for route_code, (shuttle_code, times) in TIMETABLE.items():
                shuttle_id, seats = shuttles[shuttle_code]
                for hhmm in times:
                    local = dt.datetime.combine(day, dt.time.fromisoformat(hhmm), tzinfo=tz)
                    rows.append((route_ids[route_code], shuttle_id, day.isoformat(),
                                 local.isoformat(), seats))
        conn.executemany(
            "INSERT INTO departures (route_id, shuttle_id, service_date, scheduled_at, seat_count) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT (route_id, scheduled_at) DO NOTHING", rows)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


if __name__ == "__main__":  # python -m app.seed
    from app import db
    c = db.connect(config.DATABASE_PATH)
    db.create_schema(c)
    apply_seed(c)
    print("seed applied")
