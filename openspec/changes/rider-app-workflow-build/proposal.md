# Rider App Workflow — Initial Build

## Why
# Business Requirements Document — Rider App (trip booking and live tracking)

Project: **Rider App** (code RID) · Team: Mobile · Department: Engineering
Scope of this BRD: the **book-a-trip and track-the-driver** flow. Rider
sign-up, payment methods and ratings exist already and are out of scope.

## Overview
Indnord runs a small employee shuttle fleet between the two office campuses
and the metro station. Riders currently phone a dispatcher. The Rider App
lets an employee request a seat on the next shuttle, see where it is, and
get notified when it is two minutes away.

## Goals
- Booking a seat takes three taps.
- A rider always knows whether they have a seat and when to be at the stop.
- No shuttle leaves with more riders than seats.

## Users
- **Rider**: books and cancels seats, tracks the assigned shuttle.
- **Driver** (driver app, separate): accepts the manifest, starts and ends
  the trip; shares location automatically.
- **Dispatcher**: views all trips and can cancel a shuttle run.

## Functional requirements

1. **Stops and routes**
   - The app shows the fixed routes (campus A to metro, campus B to metro and
     the reverse) with their stops and the scheduled departures for today.
   - Each departure has a shuttle with a fixed seat count.

2. **Booking**
   - A rider picks a route, a departure and a boarding stop and books one
     seat. A booking is **Confirmed** when a seat is free; otherwise the
     rider joins the **Waitlist** in order.
   - A rider may hold …

## What Changes
- Implement **Routes and Departures**
- Implement **Booking and Waitlist**
- Implement **Live Tracking and Notifications**
- Implement **Boarding and No-shows**
- Implement **Dispatcher Operations**
- Implement **Platform and Resilience**

## Impact
- Affected capabilities: routes-and-departures, booking-and-waitlist, live-tracking-and-notifications, boarding-and-no-shows, dispatcher-operations, platform-and-resilience
