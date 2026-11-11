# Platform and Resilience

## Purpose
Non-functional requirements: platform support and offline behavior.

## Requirements

### Requirement: Offline booking state cache
The system SHALL persist last known booking state and show a stale marker when offline.
_Story: Use the app offline · Spec: Offline cache and platform support · id: task-VMS2aiYMjrA_

#### Scenario: Stale state shown
- **WHEN** Device is offline
- **THEN** Last known booking state is shown with a stale marker

### Requirement: Platform compatibility
The system SHALL build and verify on Android 10+ and iOS 15+.
_Story: Use the app offline · Spec: Offline cache and platform support · id: task-b6tIiT19_U4_

#### Scenario: Runs on minimum OS
- **WHEN** App is installed on Android 10 and iOS 15
- **THEN** Booking and tracking flows work
