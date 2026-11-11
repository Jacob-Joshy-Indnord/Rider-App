# Boarding and No-shows

## Purpose
Driver manifest boarding and no-show restrictions.

## Requirements

### Requirement: Manifest and boarding endpoints
The system SHALL list confirmed riders per stop; mark a rider boarded.
_Story: Mark riders boarded · Spec: Manifest API · id: task-oClL_RGRTWA_

#### Scenario: Manifest per stop
- **WHEN** Driver requests the manifest
- **THEN** Confirmed riders are listed grouped by stop
#### Scenario: Mark boarded
- **WHEN** Driver taps a rider
- **THEN** Rider is marked boarded

### Requirement: Mark no-shows
The system SHALL mark confirmed unboarded riders No-show when shuttle leaves their stop.
_Story: No-show handling · Spec: No-show tracking and restriction · id: task-0S3Ms_MrIf0_

#### Scenario: No-show recorded
- **WHEN** Shuttle leaves a stop and a confirmed rider is not boarded
- **THEN** Rider is marked No-show

### Requirement: Waitlist-only restriction
The system SHALL after three no-shows in 30 days, force new bookings to Waitlist for 7 days.
_Story: No-show handling · Spec: No-show tracking and restriction · id: task-pK-tQ3Dml9U_

#### Scenario: Restriction applied
- **WHEN** Rider's third no-show within 30 days is recorded
- **THEN** Their bookings for the next 7 days are Waitlist only
#### Scenario: Restriction lifts
- **WHEN** 7 days have passed
- **THEN** Rider can be Confirmed again
