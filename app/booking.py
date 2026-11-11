"""Booking a seat: limits validation and atomic Confirmed/Waitlisted allocation."""
import datetime as dt
import sqlite3
from dataclasses import dataclass

from app import db

CONFIRMED = "CONFIRMED"
WAITLISTED = "WAITLISTED"
CANCELLED = "CANCELLED"
ACTIVE_STATUSES = (CONFIRMED, WAITLISTED)
MAX_FUTURE_BOOKINGS = 2


class BookingError(Exception):
    """Base for booking rejections; `code` is the stable machine-readable reason."""
    code = "booking_error"


class DepartureNotFound(BookingError):
    code = "departure_not_found"


class StopNotOnRoute(BookingError):
    code = "stop_not_on_route"


class DepartureClosed(BookingError):
    code = "departure_closed"


class DuplicateBooking(BookingError):
    code = "duplicate_booking"


class BookingLimitReached(BookingError):
    code = "booking_limit_reached"


@dataclass(frozen=True)
class Booking:
    id: int
    rider_id: str
    departure_id: int
    boarding_stop_id: int
    status: str
    waitlist_position: int | None
    created_at: dt.datetime


def create_booking(conn: sqlite3.Connection, rider_id: str, departure_id: int,
                   boarding_stop_id: int, now: dt.datetime | None = None) -> Booking:
    """Book one seat. Confirmed while seats remain, otherwise waitlisted in order.

    Rejected when the departure has left (now >= scheduled time), when the rider
    already holds an active booking on it, or when the rider already holds
    MAX_FUTURE_BOOKINGS active (Confirmed or Waitlisted) bookings on future
    departures. Cancelled bookings and past departures never count.

    The rider and the departure are locked for the whole check-count-insert
    sequence, so concurrent requests can neither over-allocate seats nor push a
    rider past the limits.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    db.begin_write(conn)
    try:
        db.lock_rider(conn, rider_id)
        departure = db.lock_departure(conn, departure_id)
        if departure is None:
            raise DepartureNotFound(f"Departure {departure_id} does not exist.")
        if now >= dt.datetime.fromisoformat(departure["scheduled_at"]):
            raise DepartureClosed(
                "Booking is closed: this shuttle has reached its departure time.")
        on_route = conn.execute(
            "SELECT 1 FROM route_stops WHERE route_id = ? AND stop_id = ?",
            (departure["route_id"], boarding_stop_id)).fetchone()
        if on_route is None:
            raise StopNotOnRoute(
                f"Stop {boarding_stop_id} is not on the route of departure {departure_id}.")
        _check_rider_limits(conn, rider_id, departure_id, now)

        confirmed = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE departure_id = ? AND status = ?",
            (departure_id, CONFIRMED)).fetchone()[0]
        if confirmed < departure["seat_count"]:
            status, position = CONFIRMED, None
        else:
            status = WAITLISTED
            position = conn.execute(
                "SELECT COALESCE(MAX(waitlist_position), 0) + 1 FROM bookings "
                "WHERE departure_id = ?", (departure_id,)).fetchone()[0]

        cur = conn.execute(
            "INSERT INTO bookings (rider_id, departure_id, boarding_stop_id, status, "
            "waitlist_position, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (rider_id, departure_id, boarding_stop_id, status, position, now.isoformat()))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return Booking(cur.lastrowid, rider_id, departure_id, boarding_stop_id, status, position, now)


def _check_rider_limits(conn: sqlite3.Connection, rider_id: str, departure_id: int,
                        now: dt.datetime) -> None:
    rows = conn.execute(
        "SELECT b.departure_id, d.scheduled_at FROM bookings b "
        "JOIN departures d ON d.id = b.departure_id "
        "WHERE b.rider_id = ? AND b.status IN (?, ?)",
        (rider_id, *ACTIVE_STATUSES)).fetchall()
    if any(r["departure_id"] == departure_id for r in rows):
        raise DuplicateBooking("You already have a booking on this departure.")
    # Compared in Python: stored timestamps carry offsets, so string order is unsafe.
    upcoming = [r for r in rows if dt.datetime.fromisoformat(r["scheduled_at"]) > now]
    if len(upcoming) >= MAX_FUTURE_BOOKINGS:
        raise BookingLimitReached(
            "You can hold at most two upcoming bookings. "
            "Cancel one before booking another.")
