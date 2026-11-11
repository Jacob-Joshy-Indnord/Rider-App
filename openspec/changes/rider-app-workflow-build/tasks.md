# Implementation Tasks

## Routes and Departures
### Browse routes and departures
- [ ] Route and departure model (`task-J685C8F43p0`)
  - [ ] Departure has seat count
  - [ ] Seeded fixed data
- [ ] Today's departures API (`task-hqaGeE8MFuI`)
  - [ ] Only today's departures
- [ ] Routes and departures UI (`task-iJKwBNilIIc`)
  - [ ] Routes displayed

## Booking and Waitlist
### Book a seat
- [ ] Atomic seat allocation (`task-_EgPLGFv03o`)
  - [ ] 13th booking waitlisted
  - [ ] No over-allocation
- [ ] Booking limits validation (`task-6kUEjuPLN_M`)
  - [ ] Third booking rejected
  - [ ] Duplicate departure rejected
  - [ ] Closed at departure
- [ ] Booking flow UI (`task-2SPD3Pv36ls`)
  - [ ] Three-tap booking
### Cancel and promotion
- [ ] Cancel booking (`task-xu3vn4ssj2o`)
  - [ ] Cancel before cutoff
  - [ ] Cancel after cutoff
- [ ] Promote waitlisted rider (`task-o8U9lZr0s14`)
  - [ ] Promotion and notice
### Manifest freeze
- [ ] Freeze manifest (`task-FtNoIhkr9AY`)
  - [ ] Manifest frozen

## Live Tracking and Notifications
### Track the shuttle
- [ ] Driver location ingestion (`task-fxgXfmffxRI`)
  - [ ] Location stored
  - [ ] Location contract enforced
  - [ ] 24h retention
- [ ] ETA calculation (`task-8GF2hynrI5U`)
  - [ ] ETA available
- [ ] Tracking map UI (`task--odS26YIDr0`)
  - [ ] Visible from T-15
  - [ ] 10s refresh
### Arrival and delay alerts
- [ ] Push notification service (`task-C46UInrJlEw`)
  - [ ] Push delivered
- [ ] Two-minute alert (`task-MYw67njcUZ0`)
  - [ ] Fires once
- [ ] Delayed banner (`task-iJgwYwZZtG8`)
  - [ ] Banner shown

## Boarding and No-shows
### Mark riders boarded
- [ ] Manifest and boarding endpoints (`task-oClL_RGRTWA`)
  - [ ] Manifest per stop
  - [ ] Mark boarded
### No-show handling
- [ ] Mark no-shows (`task-0S3Ms_MrIf0`)
  - [ ] No-show recorded
- [ ] Waitlist-only restriction (`task-pK-tQ3Dml9U`)
  - [ ] Restriction applied
  - [ ] Restriction lifts

## Dispatcher Operations
### Cancel a shuttle run
- [ ] Cancel departure (`task-TDEwgrwopME`)
  - [ ] All riders notified
- [ ] Dispatcher trips view (`task-Xnc0f1xlQrA`)
  - [ ] View and cancel

## Platform and Resilience
### Use the app offline
- [ ] Offline booking state cache (`task-VMS2aiYMjrA`)
  - [ ] Stale state shown
- [ ] Platform compatibility (`task-b6tIiT19_U4`)
  - [ ] Runs on minimum OS

