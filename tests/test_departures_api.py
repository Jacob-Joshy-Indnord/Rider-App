"""task-hqaGeE8MFuI — Today's departures API."""
import datetime as dt
import unittest
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app import db, seed
from app.main import create_app

TODAY = dt.date(2026, 11, 11)


class TodaysDeparturesApiTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.create_schema(self.conn)
        # Data for yesterday, today and tomorrow — only today's must come back.
        seed.apply_seed(self.conn, start_date=TODAY - dt.timedelta(days=1), days=3)
        app = create_app(connection_factory=lambda: self.conn, today=lambda: TODAY)
        self.client = TestClient(app)

    def tearDown(self):
        self.conn.close()

    def test_only_todays_departures_with_stops(self):
        resp = self.client.get("/api/v1/departures/today")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["service_date"], TODAY.isoformat())
        self.assertEqual(len(body["routes"]), 4)
        total = 0
        for route in body["routes"]:
            self.assertGreater(len(route["stops"]), 1)
            self.assertEqual([s["position"] for s in route["stops"]],
                             list(range(1, len(route["stops"]) + 1)))
            self.assertGreater(len(route["departures"]), 0)
            times = [d["scheduled_at"] for d in route["departures"]]
            self.assertEqual(times, sorted(times))
            for d in route["departures"]:
                when = dt.datetime.fromisoformat(d["scheduled_at"])
                self.assertEqual(when.date(), TODAY)
                self.assertGreater(d["seat_count"], 0)
                self.assertTrue(d["shuttle"]["code"])
                self.assertEqual(d["route_id"], route["id"])
                total += 1
        expected = self.conn.execute(
            "SELECT COUNT(*) FROM departures WHERE service_date = ?", (TODAY.isoformat(),)
        ).fetchone()[0]
        self.assertEqual(total, expected)

    def test_routes_without_departures_today_still_listed(self):
        self.conn.execute("DELETE FROM departures WHERE service_date = ?", (TODAY.isoformat(),))
        body = self.client.get("/api/v1/departures/today").json()
        self.assertEqual(len(body["routes"]), 4)
        self.assertTrue(all(r["departures"] == [] for r in body["routes"]))

    def test_openapi_documents_endpoint(self):
        spec = self.client.get("/openapi.json").json()
        self.assertIn("/api/v1/departures/today", spec["paths"])


class ServiceDayTest(unittest.TestCase):
    def test_today_uses_service_timezone(self):
        from app.main import service_today
        # 23:30 UTC on Nov 11 is already Nov 12 in Oslo.
        now = dt.datetime(2026, 11, 11, 23, 30, tzinfo=ZoneInfo("UTC"))
        self.assertEqual(service_today(ZoneInfo("Europe/Oslo"), now=now), dt.date(2026, 11, 12))
        self.assertEqual(service_today(ZoneInfo("UTC"), now=now), dt.date(2026, 11, 11))


if __name__ == "__main__":
    unittest.main()
