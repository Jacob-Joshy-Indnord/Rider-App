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

-- One seat request by a rider on a departure. waitlist_position is assigned
-- (monotonically per departure) only when the booking is waitlisted.
CREATE TABLE IF NOT EXISTS bookings (
    id                INTEGER PRIMARY KEY,
    rider_id          TEXT NOT NULL,
    departure_id      INTEGER NOT NULL REFERENCES departures(id),
    boarding_stop_id  INTEGER NOT NULL REFERENCES stops(id),
    status            TEXT NOT NULL CHECK (status IN ('CONFIRMED', 'WAITLISTED', 'CANCELLED')),
    waitlist_position INTEGER CHECK (waitlist_position >= 1),
    created_at        TEXT NOT NULL,
    CHECK ((status = 'WAITLISTED') = (waitlist_position IS NOT NULL) OR status = 'CANCELLED'),
    UNIQUE (departure_id, waitlist_position)
);

CREATE INDEX IF NOT EXISTS ix_bookings_departure_status ON bookings (departure_id, status);
CREATE INDEX IF NOT EXISTS ix_bookings_rider ON bookings (rider_id, status);

-- Backstop for the duplicate rule: at most one active booking per rider and departure.
CREATE UNIQUE INDEX IF NOT EXISTS ux_bookings_rider_departure_active
    ON bookings (rider_id, departure_id) WHERE status <> 'CANCELLED';
"""


def connect(path: str) -> sqlite3.Connection:
    # timeout: writers queue on the database lock instead of failing fast.
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def begin_write(conn: sqlite3.Connection) -> None:
    """Start a transaction that will write.

    SQLite: BEGIN IMMEDIATE takes the write lock up front, so a read-then-write
    sequence cannot interleave with another writer. PostgreSQL: plain BEGIN;
    serialisation comes from lock_departure's row lock.
    """
    conn.execute("BEGIN IMMEDIATE")


def lock_rider(conn: sqlite3.Connection, rider_id: str) -> None:
    """Serialise booking transactions of one rider (for the per-rider limits).

    PostgreSQL: a transaction-scoped advisory lock on the rider id, needed because
    a rider's concurrent bookings on different departures take different row
    locks. SQLite: already covered by begin_write's database lock.
    Always take this before lock_departure so lock order is consistent.
    """
    if not isinstance(conn, sqlite3.Connection):  # pragma: no cover - PostgreSQL driver
        conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (rider_id,))


def lock_departure(conn: sqlite3.Connection, departure_id: int):
    """Load a departure row, holding a lock on it until the transaction ends.

    PostgreSQL runs this with FOR UPDATE (per-departure row lock, so bookings on
    different departures do not block each other). SQLite has no row locks; the
    lock taken by begin_write covers the whole database instead.
    """
    sql = "SELECT id, route_id, scheduled_at, seat_count FROM departures WHERE id = ?"
    if not isinstance(conn, sqlite3.Connection):  # pragma: no cover - PostgreSQL driver
        sql += " FOR UPDATE"
    return conn.execute(sql, (departure_id,)).fetchone()
