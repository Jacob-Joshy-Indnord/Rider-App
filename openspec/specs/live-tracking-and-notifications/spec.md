# Live Tracking and Notifications

## Purpose
Map tracking, ETA, two-minute push alert and delayed banner.

## Requirements

### Requirement: Driver location ingestion
The system SHALL accept location updates from the driver app, stored for 24 hours only. The driver app is built separately; this backend owns the contract: an authenticated POST carrying trip id, latitude, longitude and device timestamp.
_Story: Track the shuttle · Spec: Location ingestion and ETA · id: task-fxgXfmffxRI_

#### Scenario: Location stored
- **WHEN** Driver app posts a location
- **THEN** It is stored against the trip
#### Scenario: Location contract enforced
- **GIVEN** The driver app is a separate client
- **WHEN** A location post is missing the trip id, latitude, longitude or timestamp, is out of range, or is unauthenticated
- **THEN** It is rejected with an error and nothing is stored
#### Scenario: 24h retention
- **WHEN** A location record is older than 24 hours
- **THEN** It is deleted

### Requirement: ETA calculation
The system SHALL estimate arrival at each boarding stop from latest location.
_Story: Track the shuttle · Spec: Location ingestion and ETA · id: task-8GF2hynrI5U_

#### Scenario: ETA available
- **WHEN** A location update arrives
- **THEN** ETA for each upcoming stop is recalculated

### Requirement: Tracking map UI
The system SHALL show map and ETA from 15 minutes before departure, refreshed at least every 10 seconds.
_Story: Track the shuttle · Spec: Location ingestion and ETA · id: task--odS26YIDr0_

#### Scenario: Visible from T-15
- **WHEN** Current time is 15 minutes before departure
- **THEN** Map with shuttle position and ETA to rider's stop is shown
#### Scenario: 10s refresh
- **WHEN** Tracking screen is open
- **THEN** Position refreshes at least every 10 seconds

### Requirement: Push notification service
The system SHALL send push notifications to riders on Android and iOS via Firebase Cloud Messaging (FCM) for both platforms.
_Story: Arrival and delay alerts · Spec: Notifications · id: task-C46UInrJlEw_

#### Scenario: Push delivered
- **WHEN** A notification is sent to a rider
- **THEN** It is delivered to their device via FCM (Android and iOS)

### Requirement: Two-minute alert
The system SHALL notify rider when shuttle is two minutes from their stop, deduplicated per rider per trip.
_Story: Arrival and delay alerts · Spec: Notifications · id: task-MYw67njcUZ0_

#### Scenario: Fires once
- **WHEN** Shuttle ETA to rider's stop drops to two minutes, repeatedly
- **THEN** Exactly one push is sent per rider per trip

### Requirement: Delayed banner
The system SHALL show 'delayed' banner if driver has not started trip five minutes after scheduled departure.
_Story: Arrival and delay alerts · Spec: Notifications · id: task-iJgwYwZZtG8_

#### Scenario: Banner shown
- **WHEN** Five minutes pass after scheduled departure without trip start
- **THEN** Rider sees a delayed banner
