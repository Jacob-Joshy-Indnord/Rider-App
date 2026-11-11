# Dispatcher Operations

## Purpose
Dispatcher cancels a departure and riders are notified.

## Requirements

### Requirement: Cancel departure
The system SHALL cancel departure, cancel all confirmed and waitlisted bookings, notify each rider.
_Story: Cancel a shuttle run · Spec: Departure cancellation · id: task-TDEwgrwopME_

#### Scenario: All riders notified
- **WHEN** Dispatcher cancels a departure
- **THEN** All confirmed and waitlisted bookings are cancelled and each rider is notified

### Requirement: Dispatcher trips view
The system SHALL dispatcher-role view within the mobile app to view all trips and trigger cancellation.
_Story: Cancel a shuttle run · Spec: Departure cancellation · id: task-Xnc0f1xlQrA_

#### Scenario: View and cancel
- **GIVEN** User is signed in to the mobile app with the dispatcher role
- **WHEN** Dispatcher opens the trips view
- **THEN** All trips are listed and a run can be cancelled; users without the dispatcher role cannot access the view
