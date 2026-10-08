# Rider-App

Shuttle booking workflow backend (Python 3.11 · FastAPI · pytest).

## Run

```bash
pip install -r requirements.txt
SHUTTLE_TZ=Europe/Oslo uvicorn app.main:app --reload   # SHUTTLE_TZ defaults to UTC
python -m pytest
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/departures/today` | The four fixed route directions (Campus A ⇄ Metro, Campus B ⇄ Metro) with ordered stops and today's departures, each with its shuttle and fixed seat count. |
| GET | `/book` | Trip-booking view: pick a route, one of today's departures, and a boarding stop. |
| GET | `/docs` | OpenAPI / Swagger UI. |

"Today" is the current date in `SHUTTLE_TZ`; departure times are returned as
timezone-aware ISO-8601 timestamps. The final stop of a route is
`boardable: false` (riders only get off there).

The route/stop/timetable catalog is fixed reference data in `app/catalog.py`
(route planning is out of scope). Persistent storage (PostgreSQL) arrives with
the booking stories, which need transactional seat allocation.
