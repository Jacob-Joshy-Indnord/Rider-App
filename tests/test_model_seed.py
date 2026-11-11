"""task-J685C8F43p0 — Route and departure model + seeded fixed data."""
import datetime as dt
import unittest

from app import db, repository, seed

DAY = dt.date(2026, 11, 11)


class DepartureModelTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.create_schema(self.conn)
        seed.apply_seed(self.conn, start_date=DAY, days=1)

    def tearDown(self):
        self.conn.close()

    def test_departure_has_shuttle_route_time_and_seat_count(self):
        # WHEN a departure is loaded THEN it has shuttle, route, scheduled time, seat count
        any_id = self.conn.execute("SELECT id FROM departures LIMIT 1").fetchone()[0]
        dep = repository.get_departure(self.conn, any_id)
        self.assertIsNotNone(dep)
        self.assertTrue(dep.shuttle_code)
        self.assertTrue(dep.route_code)
        self.assertIsInstance(dep.scheduled_at, dt.datetime)
        self.assertIsNotNone(dep.scheduled_at.tzinfo)
        self.assertIsInstance(dep.seat_count, int)
        self.assertGreater(dep.seat_count, 0)

    def test_seat_count_is_fixed_on_departure(self):
        # Seat capacity is snapshotted on the departure; changing the shuttle later
        # must not change capacity of an already scheduled departure.
        dep_id, shuttle_id, seats = self.conn.execute(
            "SELECT id, shuttle_id, seat_count FROM departures LIMIT 1").fetchone()
        self.conn.execute("UPDATE shuttles SET seat_count = seat_count + 5 WHERE id = ?", (shuttle_id,))
        self.assertEqual(repository.get_departure(self.conn, dep_id).seat_count, seats)

    def test_seat_count_must_be_positive(self):
        dep_id = self.conn.execute("SELECT id FROM departures LIMIT 1").fetchone()[0]
        with self.assertRaises(Exception):
            self.conn.execute("UPDATE departures SET seat_count = 0 WHERE id = ?", (dep_id,))

    def test_missing_departure_returns_none(self):
        self.assertIsNone(repository.get_departure(self.conn, 999_999))


class SeedTest(unittest.TestCase):
    def setUp(self):
        # GIVEN the system is started against an empty database
        self.conn = db.connect(":memory:")
        db.create_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def _counts(self):
        return {t: self.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("stops", "routes", "route_stops", "shuttles", "departures")}

    def test_four_route_directions_with_ordered_stops(self):
        seed.apply_seed(self.conn, start_date=DAY, days=1)
        routes = {r.code: r for r in repository.list_routes(self.conn)}
        self.assertEqual(set(routes), {"A-METRO", "METRO-A", "B-METRO", "METRO-B"})
        a_out = [s.code for s in routes["A-METRO"].stops]
        a_back = [s.code for s in routes["METRO-A"].stops]
        self.assertEqual(a_out[0], "CAMPUS-A")
        self.assertEqual(a_out[-1], "METRO")
        self.assertEqual(a_back, list(reversed(a_out)))
        b_out = [s.code for s in routes["B-METRO"].stops]
        self.assertEqual(b_out[0], "CAMPUS-B")
        self.assertEqual(b_out[-1], "METRO")
        self.assertEqual([s.code for s in routes["METRO-B"].stops], list(reversed(b_out)))
        for r in routes.values():
            self.assertEqual([s.position for s in r.stops], list(range(1, len(r.stops) + 1)))

    def test_scheduled_departures_exist_for_every_route(self):
        seed.apply_seed(self.conn, start_date=DAY, days=1)
        for r in repository.list_routes(self.conn):
            deps = repository.list_departures_for_route(self.conn, r.id, DAY)
            self.assertGreater(len(deps), 0, r.code)

    def test_reapplying_seed_creates_no_duplicates(self):
        seed.apply_seed(self.conn, start_date=DAY, days=3)
        first = self._counts()
        seed.apply_seed(self.conn, start_date=DAY, days=3)
        self.assertEqual(self._counts(), first)

    def test_rolling_seed_adds_only_new_days(self):
        seed.apply_seed(self.conn, start_date=DAY, days=1)
        one_day = self._counts()["departures"]
        seed.apply_seed(self.conn, start_date=DAY, days=2)
        self.assertEqual(self._counts()["departures"], 2 * one_day)


if __name__ == "__main__":
    unittest.main()
