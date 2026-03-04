# Booking Service

## Overview

This project implements a RESTful Booking Service for managing shared resources (e.g., meeting rooms). The service is built using FastAPI (Python) and uses SQLite for persistent storage.

The system ensures:

- No overlapping bookings for the same resource
- Idempotent booking creation
- Persistent storage across server restarts
- Basic concurrency safety
- Automated test coverage

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy
- SQLite (file-based)
- Pytest

## API Endpoints

### 1. Create Booking

**POST /bookings**

**Request Body**

```
{
  "booking_id": "string",
  "resource_id": "string",
  "start": "ISO8601 datetime",
  "end": "ISO8601 datetime",
  "user_id": "string"
}
```

**Behavior**

- Returns 201 Created if booking is successfully created.
- Returns 409 Conflict if booking overlaps with an existing booking for the same resource_id.
- Returns 200 OK if a booking with the same booking_id already exists (idempotency).
- Returns 400 Bad Request if start >= end.

### 2️. Retrieve Bookings by Resource and Date

**GET /bookings?resource_id=<id>&date=YYYY-MM-DD**

Returns all bookings for the specified resource on the given date.

**Example**

```
GET /bookings?resource_id=room1&date=2026-03-03
```

Returns:

```
[
  {
    "booking_id": "test1",
    "resource_id": "room1",
    "start": "2026-03-03T10:00:00",
    "end": "2026-03-03T11:00:00",
    "user_id": "user1"
  }
]
```

### 3️. Delete Booking

**DELETE /bookings/{booking_id}**

- Returns 200 No Content on success.
- Returns 404 Not Found if booking does not exist.

## Time Interval Handling

The system treats time intervals as:

- Start inclusive, End exclusive
- A booking occupies the interval: `[start, end)`
- A booking ending at 11:00 does NOT conflict with another starting at 11:00.
- Overlap condition is defined as: `existing.start < new.end AND existing.end > new.start`

This approach removes ambiguity at boundary times and is standard in scheduling systems.

## Idempotency Behavior

The system guarantees idempotent booking creation based on booking_id.

- If the same booking_id is submitted multiple times:
  - No duplicate rows are created.
  - Subsequent identical requests return 200 OK.
- This is enforced with a unique database constraint on booking_id and explicit lookup before insertion

## Concurrency Handling

To prevent race conditions (e.g., two overlapping bookings submitted simultaneously), the system:

- Uses database-level transactions
- Uses BEGIN IMMEDIATE to acquire a write lock in SQLite
- Performs overlap check and insert within the same transaction

This makes it so that only one overlapping booking can succeed and the other request receives 409 Conflict

## Persistence Strategy

The system uses file-based SQLite (`sqlite:///./bookings.db`).

**Why SQLite?**

- Lightweight and embedded
- Data persists across server restarts
- recommended in the take home project requirements from MIC

## Design Decisions & Tradeoffs

1. **Transaction-Based Concurrency**
   - Used BEGIN IMMEDIATE to ensure atomic overlap check and insert.
   - Tradeoff: SQLite uses coarse locking but it is acceptable for this scale.
3. **Start Inclusive, End Exclusive**
   - Prevents ambiguous boundary conflicts.
4. **Explicit Overlap Query**
   - Instead of relying only on constraints, the overlap logic is explicit for clarity and maintainability.

## Automated Tests

The project includes automated tests covering:

- Overlap Detection: Ensures overlapping bookings return 409.
- Idempotency: Ensures duplicate booking_id returns 200. Ensures no duplicate records are created.
- Concurrency Test: Simulates simultaneous overlapping booking attempts and verifies that only one succeeds.
- Basic API Behavior: Create booking success, Retrieve bookings, Delete booking, Validation errors.

The test database is reset before each test to ensure isolation.

## How to Run the Service

1️⃣ **Install Dependencies**

```
pip install -r requirements.txt
```

2️⃣ **Run Server**

```
uvicorn app.main:app --reload
```

The API will be available at:

- http://127.0.0.1:8000
- To run manual tests go to -> Swagger UI: http://127.0.0.1:8000/docs

## How to Run Tests

```
python -m pytest
```

All tests should pass consistently across multiple runs.

## Assumptions

- All timestamps are provided in ISO8601 format.
- Timezone handling is not implemented (assumed consistent input).
- Each booking_id is globally unique.
- System designed for small-to-medium scale usage.

## What I Would Improve With More Time

- Add timezone-aware datetime handling
- Add pagination for GET endpoint
- Add database indexing optimization
- Add Docker support
- Migrate to PostgreSQL for better concurrency scalability
- Add structured logging
- Add request validation middleware
- Add rate limiting

## Project Structure

```
app/
 ├── main.py
 ├── models.py
 ├── schemas.py
 ├── crud.py
 ├── database.py
tests/
 ├── test_booking.py
```

## Conclusion

This booking system project provides:

- Correct overlap handling
- Safe idempotent behavior
- Persistent storage
- Basic concurrency protection
- Comprehensive automated tests

The system is designed to be simple, correct, and extensible.
