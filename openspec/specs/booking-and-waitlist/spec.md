# Booking and Waitlist

## Purpose
Book, cancel and waitlist seats with limits, promotion and concurrency safety.

## Requirements

### Requirement: Atomic seat allocation
The system SHALL create booking as Confirmed or Waitlisted in order, using transactional/locked allocation so concurrent requests never over-allocate.
_Story: Book a seat · Spec: Booking and waitlist allocation · id: task-_EgPLGFv03o_

#### Scenario: 13th booking waitlisted
- **WHEN** A 13th rider books a full 12-seat departure
- **THEN** The booking is Waitlisted in order
#### Scenario: No over-allocation
- **WHEN** Many riders book the last seat concurrently
- **THEN** Exactly one is Confirmed and others are Waitlisted

### Requirement: Booking limits validation
The system SHALL reject a booking if rider has two future bookings or already has one on the same departure; reject after departure time.
_Story: Book a seat · Spec: Booking and waitlist allocation · id: task-6kUEjuPLN_M_

#### Scenario: Third booking rejected
- **WHEN** A rider with two future bookings books a third
- **THEN** A clear error is returned and no booking is created
#### Scenario: Duplicate departure rejected
- **WHEN** A rider books a departure they already hold
- **THEN** The booking is rejected with an error
#### Scenario: Closed at departure
- **WHEN** A booking is attempted at or after departure time
- **THEN** It is rejected

### Requirement: Booking flow UI
The system SHALL three-tap flow: route, departure, boarding stop, showing Confirmed or Waitlist status.
_Story: Book a seat · Spec: Booking and waitlist allocation · id: task-2SPD3Pv36ls_

#### Scenario: Three-tap booking
- **WHEN** Rider books from the departures list
- **THEN** Booking completes in three taps and status is displayed

### Requirement: Cancel booking
The system SHALL cancel endpoint enforcing the 5-minute cutoff.
_Story: Cancel and promotion · Spec: Cancellation and waitlist promotion · id: task-xu3vn4ssj2o_

#### Scenario: Cancel before cutoff
- **WHEN** Rider cancels more than 5 minutes before departure
- **THEN** Booking is cancelled
#### Scenario: Cancel after cutoff
- **WHEN** Rider cancels within 5 minutes of departure
- **THEN** Cancellation is rejected

### Requirement: Promote waitlisted rider
The system SHALL on confirmed cancellation promote first waitlisted rider to Confirmed and send a notification.
_Story: Cancel and promotion · Spec: Cancellation and waitlist promotion · id: task-o8U9lZr0s14_

#### Scenario: Promotion and notice
- **WHEN** A confirmed seat on a full departure is cancelled
- **THEN** First waitlisted rider becomes Confirmed and receives a notification

### Requirement: Freeze manifest
The system SHALL at departure time block booking, cancellation and promotion changes.
_Story: Manifest freeze · Spec: Booking close at departure · id: task-FtNoIhkr9AY_

#### Scenario: Manifest frozen
- **WHEN** Scheduled departure time passes
- **THEN** No bookings or promotions change the manifest
