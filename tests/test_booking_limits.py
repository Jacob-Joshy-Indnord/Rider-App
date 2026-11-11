"""task-6kUEjuPLN_M — Booking limits validation."""
import datetime as dt
import os
import tempfile
import threading
import unittest

from fastapi.testclient import TestClient

from app import booking, db, seed
from app.main import create_app

DAY = dt.date(2026, 11, 11)
UTC = dt.timezone.utc
EARLY = dt.datetime(2026, 11, 11, 0, 0, tzinfo=UTC)


def _departures(conn):
    """All seeded departures as (id, scheduled_at, first stop id), earliest first."""
    rows = conn.execute(
        "SELECT d.id, d.scheduled_at, rs.stop_id FROM departures d "
        "JOIN route_stops rs ON rs.route_id = d.route_id AND rs.position = 1 "
        "ORDER BY d.scheduled_at, d.id").fetchall()
    return [(r["id"], dt.datetime.fromisoformat(r["scheduled_at"]), r["stop_id"]) for r in rows]


def _count(conn):
    return conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]


class LimitsTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.create_schema(self.conn)
        seed.apply_seed(self.conn, start_date=DAY, days=1)
        self.deps = _departures(self.conn)

    def tearDown(self):
        self.conn.close()

    def book(self, rider, idx, now=EARLY):
        dep_id, _, stop = self.deps[idx]
        return booking.create_booking(self.conn, rider, dep_id, stop, now=now)

    def cancel(self, b):
        self.conn.execute("UPDATE bookings SET status = 'CANCELLED' WHERE id = ?", (b.id,))

    # Scenario: Third booking rejected
    def test_third_future_booking_rejected_with_clear_error(self):
        self.book("r", 0)
        self.book("r", 1)
        before = _count(self.conn)
        with self.assertRaises(booking.BookingLimitReached) as ctx:
            self.book("r", 2)
        self.assertEqual(ctx.exception.code, "booking_limit_reached")
        self.assertIn("two", str(ctx.exception))
        self.assertEqual(_count(self.conn), before)

    def test_waitlisted_booking_counts_toward_limit(self):
        dep_id, _, stop = self.deps[0]
        for i in range(12):
            booking.create_booking(self.conn, f"filler-{i}", dep_id, stop, now=EARLY)
        self.assertEqual(self.book("r", 0).status, booking.WAITLISTED)
        self.book("r", 1)
        with self.assertRaises(booking.BookingLimitReached):
            self.book("r", 2)

    def test_cancelled_booking_does_not_count(self):
        self.cancel(self.book("r", 0))
        self.book("r", 1)
        self.assertEqual(self.book("r", 2).status, booking.CONFIRMED)

    def test_past_departure_does_not_count(self):
        first_time = self.deps[0][1]
        self.book("r", 0)
        later = first_time + dt.timedelta(minutes=1)
        future = [i for i, d in enumerate(self.deps) if d[1] > later][:2]
        self.book("r", future[0], now=later)
        self.book("r", future[1], now=later)  # booking on deps[0] is now in the past

    def test_limit_is_per_rider(self):
        self.book("r1", 0)
        self.book("r1", 1)
        self.assertEqual(self.book("r2", 2).status, booking.CONFIRMED)

    # Scenario: Duplicate departure rejected
    def test_duplicate_departure_rejected(self):
        self.book("r", 0)
        before = _count(self.conn)
        with self.assertRaises(booking.DuplicateBooking) as ctx:
            self.book("r", 0)
        self.assertEqual(ctx.exception.code, "duplicate_booking")
        self.assertEqual(_count(self.conn), before)

    def test_duplicate_reported_before_limit(self):
        self.book("r", 0)
        self.book("r", 1)
        with self.assertRaises(booking.DuplicateBooking):
            self.book("r", 0)

    def test_rebook_after_cancel_allowed(self):
        self.cancel(self.book("r", 0))
        self.assertEqual(self.book("r", 0).status, booking.CONFIRMED)

    def test_db_rejects_duplicate_active_booking(self):
        b = self.book("r", 0)
        with self.assertRaises(Exception):
            self.conn.execute(
                "INSERT INTO bookings (rider_id, departure_id, boarding_stop_id, status, "
                "created_at) VALUES (?, ?, ?, 'CONFIRMED', ?)",
                ("r", b.departure_id, b.boarding_stop_id, EARLY.isoformat()))

    # Scenario: Closed at departure
    def test_rejected_at_departure_time(self):
        _, when, _ = self.deps[0]
        with self.assertRaises(booking.DepartureClosed) as ctx:
            self.book("r", 0, now=when)
        self.assertEqual(ctx.exception.code, "departure_closed")
        self.assertEqual(_count(self.conn), 0)

    def test_rejected_after_departure_time(self):
        _, when, _ = self.deps[0]
        with self.assertRaises(booking.DepartureClosed):
            self.book("r", 0, now=when + dt.timedelta(seconds=1))

    def test_allowed_just_before_departure(self):
        _, when, _ = self.deps[0]
        self.assertEqual(self.book("r", 0, now=when - dt.timedelta(seconds=1)).status,
                         booking.CONFIRMED)

    def test_closed_compares_across_timezones(self):
        _, when, _ = self.deps[0]
        same_instant_elsewhere = when.astimezone(dt.timezone(dt.timedelta(hours=-5)))
        with self.assertRaises(booking.DepartureClosed):
            self.book("r", 0, now=same_instant_elsewhere)


class ConcurrentLimitTest(unittest.TestCase):
    """One rider tapping many times at once must not exceed the limits."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "limits.db")
        conn = db.connect(self.path)
        db.create_schema(conn)
        seed.apply_seed(conn, start_date=DAY, days=1)
        self.deps = _departures(conn)
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def _race(self, targets):
        barrier = threading.Barrier(len(targets))
        ok, rejected, errors = [], [], []

        def worker(dep):
            conn = db.connect(self.path)
            try:
                barrier.wait()
                ok.append(booking.create_booking(conn, "tapper", dep[0], dep[2], now=EARLY))
            except booking.BookingError as exc:
                rejected.append(exc)
            except Exception as exc:  # pragma: no cover
                errors.append(exc)
            finally:
                conn.close()

        threads = [threading.Thread(target=worker, args=(d,)) for d in targets]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        return ok, rejected

    def test_concurrent_bookings_on_different_departures_stop_at_two(self):
        ok, rejected = self._race(self.deps[:10])
        self.assertEqual(len(ok), 2)
        self.assertTrue(all(isinstance(e, booking.BookingLimitReached) for e in rejected))
        self.assertEqual(len(rejected), 8)

    def test_concurrent_taps_on_same_departure_create_one_booking(self):
        ok, rejected = self._race([self.deps[0]] * 10)
        self.assertEqual(len(ok), 1)
        self.assertTrue(all(isinstance(e, booking.DuplicateBooking) for e in rejected))


class LimitsApiTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.create_schema(self.conn)
        seed.apply_seed(self.conn, start_date=DAY, days=1)
        self.deps = _departures(self.conn)
        self.now = EARLY
        app = create_app(connection_factory=lambda: self.conn,
                         today=lambda: DAY, now=lambda: self.now)
        self.client = TestClient(app)

    def tearDown(self):
        self.conn.close()

    def post(self, idx, rider="r"):
        dep_id, _, stop = self.deps[idx]
        return self.client.post("/api/v1/bookings",
                                json={"departure_id": dep_id, "boarding_stop_id": stop},
                                headers={"X-Rider-Id": rider})

    def assertError(self, resp, http_status, code):
        self.assertEqual(resp.status_code, http_status, resp.text)
        detail = resp.json()["detail"]
        self.assertEqual(detail["code"], code)
        self.assertTrue(detail["message"])

    def test_third_booking_is_409_limit_reached(self):
        self.assertEqual(self.post(0).status_code, 201)
        self.assertEqual(self.post(1).status_code, 201)
        self.assertError(self.post(2), 409, "booking_limit_reached")

    def test_duplicate_is_409(self):
        self.post(0)
        self.assertError(self.post(0), 409, "duplicate_booking")

    def test_closed_is_409(self):
        self.now = self.deps[0][1]
        self.assertError(self.post(0), 409, "departure_closed")


if __name__ == "__main__":
    unittest.main()
