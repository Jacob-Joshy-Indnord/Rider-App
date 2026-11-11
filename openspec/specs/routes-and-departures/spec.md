# Routes and Departures

## Purpose
Show fixed routes, stops and today's scheduled departures with seat counts.

## Requirements

### Requirement: Route and departure model
The system SHALL define routes (campus A/metro, campus B/metro, both directions), ordered stops, departures with shuttle and fixed seat count. Routes, stops and schedules are loaded from seeded fixed data (no admin UI or import); route planning is out of scope.
_Story: Browse routes and departures · Spec: Route and departure data · id: task-J685C8F43p0_

#### Scenario: Departure has seat count
- **WHEN** A departure is loaded
- **THEN** It has a shuttle, route, scheduled time and fixed seat count
#### Scenario: Seeded fixed data
- **GIVEN** The system is started against an empty database
- **WHEN** The seed data is applied
- **THEN** The campus A/metro and campus B/metro routes in both directions, their ordered stops and scheduled departures exist, and re-applying the seed does not create duplicates

### Requirement: Today's departures API
The system SHALL endpoint returning routes, stops and today's scheduled departures.
_Story: Browse routes and departures · Spec: Route and departure data · id: task-hqaGeE8MFuI_

#### Scenario: Only today's departures
- **WHEN** The client requests departures
- **THEN** Only today's departures with their stops are returned

### Requirement: Routes and departures UI
The system SHALL screen showing routes, stops and today's departures.
_Story: Browse routes and departures · Spec: Routes screen · id: task-iJKwBNilIIc_

#### Scenario: Routes displayed
- **WHEN** Rider opens the app
- **THEN** All four route directions with stops and today's departures are shown
