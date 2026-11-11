"""Database connection and schema.

The DDL is kept to portable SQL (identity via INTEGER PRIMARY KEY, UNIQUE,
CHECK, ON CONFLICT DO NOTHING) so it runs on SQLite locally and maps 1:1 to
PostgreSQL in deployment.
"""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS stops (
    id    INTEGER PRIMARY KEY,
    code  TEXT NOT NULL UNIQUE,
    name  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS routes (
    id          INTEGER PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    origin_stop_id      INTEGER NOT NULL REFERENCES stops(id),
    destination_stop_id INTEGER NOT NULL REFERENCES stops(id),
    CHECK (origin_stop_id <> destination_stop_id)
);

-- Ordered stops of a route; position is 1-based.
CREATE TABLE IF NOT EXISTS route_stops (
    route_id  INTEGER NOT NULL REFERENCES routes(id),
    stop_id   INTEGER NOT NULL REFERENCES stops(id),
    position  INTEGER NOT NULL CHECK (position >= 1),
    PRIMARY KEY (route_id, position),
    UNIQUE (route_id, stop_id)
);

CREATE TABLE IF NOT EXISTS shuttles (
    id          INTEGER PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    seat_count  INTEGER NOT NULL CHECK (seat_count > 0)
);

-- seat_count is copied from the shuttle when the departure is created and is
-- fixed thereafter: it is the capacity bookings are allocated against.
CREATE TABLE IF NOT EXISTS departures (
    id            INTEGER PRIMARY KEY,
    route_id      INTEGER NOT NULL REFERENCES routes(id),
    shuttle_id    INTEGER NOT NULL REFERENCES shuttles(id),
    service_date  TEXT NOT NULL,          -- ISO date in SERVICE_TZ
    scheduled_at  TEXT NOT NULL,          -- ISO 8601 timestamp with offset
    seat_count    INTEGER NOT NULL CHECK (seat_count > 0),
    UNIQUE (route_id, scheduled_at)
);

CREATE INDEX IF NOT EXISTS ix_departures_service_date
    ON departures (service_date, route_id, scheduled_at);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
