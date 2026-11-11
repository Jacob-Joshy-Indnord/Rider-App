"""task-_EgPLGFv03o — Atomic seat allocation."""
import datetime as dt
import os
import tempfile
import threading
import unittest

from fastapi.testclient import TestClient

from app import booking, db, seed
from app.main import create_app

DAY = dt.date(2026, 11, 11)
# Well before any seeded departure on DAY, so booking is open.
EARLY = dt.datetime(2026, 11, 11, 0, 0, tzinfo=dt.timezone.utc)


def _first_departure(conn):
    row = conn.execute(
        "SELECT d.id, d.seat_count, rs.stop_id FROM departures d "
        "JOIN route_stops rs ON rs.route_id = d.route_id AND rs.position = 1 "
        "ORDER BY d.scheduled_at LIMIT 1").fetchone()
    return row["id"], row["seat_count"], row["stop_id"]


class AllocationTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.create_schema(self.conn)
        seed.apply_seed(self.conn, start_date=DAY, days=1)
        self.dep_id, self.seats, self.stop_id = _first_departure(self.conn)

    def tearDown(self):
        self.conn.close()

    def book(self, rider):
        return booking.create_booking(self.conn, rider, self.dep_id, self.stop_id, now=EARLY)

    def test_confirmed_while_seats_free(self):
        b = self.book("rider-1")
        self.assertEqual(b.status, booking.CONFIRMED)
        self.assertIsNone(b.waitlist_position)

    def test_13th_booking_on_12_seat_departure_is_waitlisted_in_order(self):
        self.assertEqual(self.seats, 12)
        results = [self.book(f"rider-{i}") for i in range(1, 15)]
        self.assertTrue(all(b.status == booking.CONFIRMED for b in results[:12]))
        self.assertEqual(results[12].status, booking.WAITLISTED)
        self.assertEqual(results[12].waitlist_position, 1)
        self.assertEqual(results[13].status, booking.WAITLISTED)
        self.assertEqual(results[13].waitlist_position, 2)

    def test_unknown_departure_rejected(self):
        with self.assertRaises(booking.DepartureNotFound):
            booking.create_booking(self.conn, "r", 999_999, self.stop_id, now=EARLY)

    def test_stop_not_on_route_rejected(self):
        other_stop = self.conn.execute(
            "SELECT id FROM stops WHERE id NOT IN "
            "(SELECT stop_id FROM route_stops WHERE route_id = "
            " (SELECT route_id FROM departures WHERE id = ?))", (self.dep_id,)).fetchone()[0]
        with self.assertRaises(booking.StopNotOnRoute):
            booking.create_booking(self.conn, "r", self.dep_id, other_stop, now=EARLY)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0], 0)


class ConcurrentAllocationTest(unittest.TestCase):
    """Many riders race for the last seat, each on its own DB connection."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "race.db")
        conn = db.connect(self.path)
        db.create_schema(conn)
        seed.apply_seed(conn, start_date=DAY, days=1)
        self.dep_id, self.seats, self.stop_id = _first_departure(conn)
        for i in range(self.seats - 1):  # leave exactly one seat
            booking.create_booking(conn, f"pre-{i}", self.dep_id, self.stop_id, now=EARLY)
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_exactly_one_confirmed_rest_waitlisted(self):
        racers = 20
        barrier = threading.Barrier(racers)
        results, errors = [], []

        def worker(i):
            conn = db.connect(self.path)
            try:
                barrier.wait()
                results.append(booking.create_booking(
                    conn, f"racer-{i}", self.dep_id, self.stop_id, now=EARLY))
            except Exception as exc:  # pragma: no cover - surfaced below
                errors.append(exc)
            finally:
                conn.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(racers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        statuses = [b.status for b in results]
        self.assertEqual(statuses.count(booking.CONFIRMED), 1)
        self.assertEqual(statuses.count(booking.WAITLISTED), racers - 1)
        positions = sorted(b.waitlist_position for b in results if b.status == booking.WAITLISTED)
        self.assertEqual(positions, list(range(1, racers)))

        conn = db.connect(self.path)
        confirmed = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE departure_id = ? AND status = ?",
            (self.dep_id, booking.CONFIRMED)).fetchone()[0]
        conn.close()
        self.assertEqual(confirmed, self.seats)


class BookingApiTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.create_schema(self.conn)
        seed.apply_seed(self.conn, start_date=DAY, days=1)
        self.dep_id, _, self.stop_id = _first_departure(self.conn)
        app = create_app(connection_factory=lambda: self.conn,
                         today=lambda: DAY, now=lambda: EARLY)
        self.client = TestClient(app)

    def tearDown(self):
        self.conn.close()

    def post(self, rider, **body):
        payload = {"departure_id": self.dep_id, "boarding_stop_id": self.stop_id, **body}
        return self.client.post("/api/v1/bookings", json=payload, headers={"X-Rider-Id": rider})

    def test_create_booking_returns_201_with_status(self):
        resp = self.post("rider-1")
        self.assertEqual(resp.status_code, 201, resp.text)
        body = resp.json()
        self.assertEqual(body["status"], "CONFIRMED")
        self.assertIsNone(body["waitlist_position"])
        self.assertEqual(body["departure_id"], self.dep_id)
        self.assertEqual(body["boarding_stop_id"], self.stop_id)

    def test_unknown_departure_is_404(self):
        resp = self.post("rider-1", departure_id=999_999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["detail"]["code"], "departure_not_found")

    def test_stop_not_on_route_is_422(self):
        resp = self.post("rider-1", boarding_stop_id=999_999)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["detail"]["code"], "stop_not_on_route")

    def test_missing_rider_header_is_rejected(self):
        resp = self.client.post("/api/v1/bookings",
                                json={"departure_id": self.dep_id, "boarding_stop_id": self.stop_id})
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
