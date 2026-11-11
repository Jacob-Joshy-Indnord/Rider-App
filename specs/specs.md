# Approved Specifications: Rider App Workflow

Authoritative specs are written under /workspace/openspec/ in OpenSpec format: capability specs in openspec/specs/<capability>/spec.md (requirements + scenarios) and the implementation checklist in openspec/changes/<change>/tasks.md. A JSON copy is at /workspace/specs/spec_project.json. Implement ONLY the approved items below and satisfy every acceptance scenario.

If you build a runnable web app, serve it on 0.0.0.0:8080 so it can be opened in the Live Preview (the platform proxies that port).

## Build protocol
- Maintain a machine-readable build report at /workspace/specs/build_report.json with this exact shape: {"tasks": [{"id": "task-…", "status": "done", "files": ["path/to/file", "…"]}]}. Update it EVERY time you finish a task: set its status to "done" and list every file you created or modified for it (repo-relative paths). The platform reads this file back to mark tasks done and to link the produced code into the traceability graph.
- When delegating to sub-agents, include the task id (task-…) and its acceptance scenarios verbatim in the delegation message, and record the files they report back in the build report.

## Items marked “needs a look”
The BRD covers these only loosely, so the spec writer had to interpret them. For each one, decide the interpretation you build, record it in the build report as an "assumptions" list next to "tasks" — [{"id": "<node id>", "assumption": "…"}] — and state it in your final message so the reviewer can check it.
- Task `task-_EgPLGFv03o`: Atomic seat allocation — BRD states the outcome only; locking mechanism (row lock, serializable txn, queue) is an assumption.
- Task `task-6kUEjuPLN_M`: Booking limits validation — Assumed waitlisted bookings count toward the two-booking limit and that cancelled ones do not.
- Task `task-2SPD3Pv36ls`: Booking flow UI — 'Three taps' interpreted as select departure, select stop, confirm.
- Spec `spec-paWYjbUfZWY`: Booking close at departure — Assumed freeze is by scheduled time, not actual trip start.
- Task `task-FtNoIhkr9AY`: Freeze manifest — Assumed waitlist is not promoted after freeze.
- Task `task-8GF2hynrI5U`: ETA calculation — BRD gives no ETA method; assumed routing/distance-based estimate.
- Spec `spec-AgsxmvuBxOI`: Manifest API — Driver app is separate; assumed this app's backend exposes the endpoints.
- Task `task-0S3Ms_MrIf0`: Mark no-shows — 'Leaves their stop' assumed detected from driver location or driver action.
- Task `task-pK-tQ3Dml9U`: Waitlist-only restriction — Assumed the 7 days start at the third no-show and existing bookings are unaffected.

## Epic: Routes and Departures
Show fixed routes, stops and today's scheduled departures with seat counts.
### Story: Browse routes and departures
_As a rider, I want to see routes, stops and today's departures, so that I can choose a shuttle to book_
#### Spec: Route and departure data
Read-only API and data model for fixed routes, stops, departures and per-departure seat capacity.
- **Task** (`task-J685C8F43p0`): Route and departure model
  - Define routes (campus A/metro, campus B/metro, both directions), ordered stops, departures with shuttle and fixed seat count. Routes, stops and schedules are loaded from seeded fixed data (no admin UI or import); route planning is out of scope.
  - [ ] WHEN A departure is loaded THEN It has a shuttle, route, scheduled time and fixed seat count
  - [ ] WHEN The seed data is applied THEN The campus A/metro and campus B/metro routes in both directions, their ordered stops and scheduled departures exist, and re-applying the seed does not create duplicates
- **Task** (`task-hqaGeE8MFuI`): Today's departures API
  - Endpoint returning routes, stops and today's scheduled departures.
  - [ ] WHEN The client requests departures THEN Only today's departures with their stops are returned
#### Spec: Routes screen
Mobile UI listing routes, stops and departures.
- **Task** (`task-iJKwBNilIIc`): Routes and departures UI
  - Screen showing routes, stops and today's departures.
  - [ ] WHEN Rider opens the app THEN All four route directions with stops and today's departures are shown

## Epic: Booking and Waitlist
Book, cancel and waitlist seats with limits, promotion and concurrency safety.
### Story: Book a seat
_As a rider, I want to book a seat on a departure at my boarding stop, so that I know I have a seat_
#### Spec: Booking and waitlist allocation
Atomic seat allocation: Confirmed if a seat is free, otherwise ordered Waitlist; enforce booking limits.
- **Task** (`task-_EgPLGFv03o`): Atomic seat allocation
  - Create booking as Confirmed or Waitlisted in order, using transactional/locked allocation so concurrent requests never over-allocate.
  - [ ] WHEN A 13th rider books a full 12-seat departure THEN The booking is Waitlisted in order
  - [ ] WHEN Many riders book the last seat concurrently THEN Exactly one is Confirmed and others are Waitlisted
- **Task** (`task-6kUEjuPLN_M`): Booking limits validation
  - Reject a booking if rider has two future bookings or already has one on the same departure; reject after departure time.
  - [ ] WHEN A rider with two future bookings books a third THEN A clear error is returned and no booking is created
  - [ ] WHEN A rider books a departure they already hold THEN The booking is rejected with an error
  - [ ] WHEN A booking is attempted at or after departure time THEN It is rejected
- **Task** (`task-2SPD3Pv36ls`): Booking flow UI
  - Three-tap flow: route, departure, boarding stop, showing Confirmed or Waitlist status.
  - [ ] WHEN Rider books from the departures list THEN Booking completes in three taps and status is displayed
### Story: Cancel and promotion
_As a rider, I want to cancel my booking, so that my seat can go to someone else_
#### Spec: Cancellation and waitlist promotion
Cancellation allowed until 5 minutes before departure; confirmed cancellation promotes first waitlisted rider.
- **Task** (`task-xu3vn4ssj2o`): Cancel booking
  - Cancel endpoint enforcing the 5-minute cutoff.
  - [ ] WHEN Rider cancels more than 5 minutes before departure THEN Booking is cancelled
  - [ ] WHEN Rider cancels within 5 minutes of departure THEN Cancellation is rejected
- **Task** (`task-o8U9lZr0s14`): Promote waitlisted rider
  - On confirmed cancellation promote first waitlisted rider to Confirmed and send a notification.
  - [ ] WHEN A confirmed seat on a full departure is cancelled THEN First waitlisted rider becomes Confirmed and receives a notification
### Story: Manifest freeze
_As a driver, I want a frozen manifest at departure, so that no shuttle leaves over capacity_
#### Spec: Booking close at departure
Freeze manifest at scheduled departure time.
- **Task** (`task-FtNoIhkr9AY`): Freeze manifest
  - At departure time block booking, cancellation and promotion changes.
  - [ ] WHEN Scheduled departure time passes THEN No bookings or promotions change the manifest

## Epic: Live Tracking and Notifications
Map tracking, ETA, two-minute push alert and delayed banner.
### Story: Track the shuttle
_As a rider, I want to see the shuttle on a map with an ETA, so that I know when to be at the stop_
#### Spec: Location ingestion and ETA
Receive driver location, compute ETA to each boarding stop, and serve it to riders.
- **Task** (`task-fxgXfmffxRI`): Driver location ingestion
  - Accept location updates from the driver app, stored for 24 hours only. The driver app is built separately; this backend owns the contract: an authenticated POST carrying trip id, latitude, longitude and device timestamp.
  - [ ] WHEN Driver app posts a location THEN It is stored against the trip
  - [ ] WHEN A location post is missing the trip id, latitude, longitude or timestamp, is out of range, or is unauthenticated THEN It is rejected with an error and nothing is stored
  - [ ] WHEN A location record is older than 24 hours THEN It is deleted
- **Task** (`task-8GF2hynrI5U`): ETA calculation
  - Estimate arrival at each boarding stop from latest location.
  - [ ] WHEN A location update arrives THEN ETA for each upcoming stop is recalculated
- **Task** (`task--odS26YIDr0`): Tracking map UI
  - Show map and ETA from 15 minutes before departure, refreshed at least every 10 seconds.
  - [ ] WHEN Current time is 15 minutes before departure THEN Map with shuttle position and ETA to rider's stop is shown
  - [ ] WHEN Tracking screen is open THEN Position refreshes at least every 10 seconds
### Story: Arrival and delay alerts
_As a rider, I want alerts when the shuttle is near or late, so that I'm at the stop on time_
#### Spec: Notifications
Push delivery, two-minute alert once per rider per trip, and delayed banner.
- **Task** (`task-C46UInrJlEw`): Push notification service
  - Send push notifications to riders on Android and iOS via Firebase Cloud Messaging (FCM) for both platforms.
  - [ ] WHEN A notification is sent to a rider THEN It is delivered to their device via FCM (Android and iOS)
- **Task** (`task-MYw67njcUZ0`): Two-minute alert
  - Notify rider when shuttle is two minutes from their stop, deduplicated per rider per trip.
  - [ ] WHEN Shuttle ETA to rider's stop drops to two minutes, repeatedly THEN Exactly one push is sent per rider per trip
- **Task** (`task-iJgwYwZZtG8`): Delayed banner
  - Show 'delayed' banner if driver has not started trip five minutes after scheduled departure.
  - [ ] WHEN Five minutes pass after scheduled departure without trip start THEN Rider sees a delayed banner

## Epic: Boarding and No-shows
Driver manifest boarding and no-show restrictions.
### Story: Mark riders boarded
_As a driver, I want a manifest per stop where I can mark riders boarded, so that I know who is on board_
#### Spec: Manifest API
Backend endpoints serving the manifest and recording boarding for the driver app.
- **Task** (`task-oClL_RGRTWA`): Manifest and boarding endpoints
  - List confirmed riders per stop; mark a rider boarded.
  - [ ] WHEN Driver requests the manifest THEN Confirmed riders are listed grouped by stop
  - [ ] WHEN Driver taps a rider THEN Rider is marked boarded
### Story: No-show handling
_As a dispatcher, I want repeat no-shows restricted, so that seats are not wasted_
#### Spec: No-show tracking and restriction
Mark no-shows when shuttle leaves a stop and apply waitlist-only restriction.
- **Task** (`task-0S3Ms_MrIf0`): Mark no-shows
  - Mark confirmed unboarded riders No-show when shuttle leaves their stop.
  - [ ] WHEN Shuttle leaves a stop and a confirmed rider is not boarded THEN Rider is marked No-show
- **Task** (`task-pK-tQ3Dml9U`): Waitlist-only restriction
  - After three no-shows in 30 days, force new bookings to Waitlist for 7 days.
  - [ ] WHEN Rider's third no-show within 30 days is recorded THEN Their bookings for the next 7 days are Waitlist only
  - [ ] WHEN 7 days have passed THEN Rider can be Confirmed again

## Epic: Dispatcher Operations
Dispatcher cancels a departure and riders are notified.
### Story: Cancel a shuttle run
_As a dispatcher, I want to cancel a departure, so that riders are informed and bookings cleared_
#### Spec: Departure cancellation
Cancel departure, cancel all bookings and notify riders.
- **Task** (`task-TDEwgrwopME`): Cancel departure
  - Cancel departure, cancel all confirmed and waitlisted bookings, notify each rider.
  - [ ] WHEN Dispatcher cancels a departure THEN All confirmed and waitlisted bookings are cancelled and each rider is notified
- **Task** (`task-Xnc0f1xlQrA`): Dispatcher trips view
  - Dispatcher-role view within the mobile app to view all trips and trigger cancellation.
  - [ ] WHEN Dispatcher opens the trips view THEN All trips are listed and a run can be cancelled; users without the dispatcher role cannot access the view

## Epic: Platform and Resilience
Non-functional requirements: platform support and offline behavior.
### Story: Use the app offline
_As a rider, I want to see my last known booking state offline, so that I still know my seat status_
#### Spec: Offline cache and platform support
Cache booking state locally with stale marker; support Android 10+ and iOS 15+.
- **Task** (`task-VMS2aiYMjrA`): Offline booking state cache
  - Persist last known booking state and show a stale marker when offline.
  - [ ] WHEN Device is offline THEN Last known booking state is shown with a stale marker
- **Task** (`task-b6tIiT19_U4`): Platform compatibility
  - Build and verify on Android 10+ and iOS 15+.
  - [ ] WHEN App is installed on Android 10 and iOS 15 THEN Booking and tracking flows work
