# crud.py {
#     - Overlap logic
#     - Insert booking
#     - Query bookings
#     - Idempotency handling
# }

from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from datetime import datetime, timedelta
import app.models, app.schemas
from sqlalchemy.exc import IntegrityError


### Create Booking

def create_booking(db: Session, booking: app.schemas.BookingCreate):
    
    # Start IMMEDIATE transaction to prevent race condition
    db.execute(text("BEGIN IMMEDIATE"))
    
    # start < end
    if booking.start >= booking.end:
        raise ValueError("Start time must be before end time")

    # check idempotency (existing booking)
    existing_booking = db.query(app.models.Booking).filter(
        app.models.Booking.booking_id == booking.booking_id
    ).first()

    if existing_booking:
        return existing_booking, "exists"

    # overlap detection (half-open interval logic)
    overlap_bookings = db.query(app.models.Booking).filter(
        app.models.Booking.resource_id == booking.resource_id,
        app.models.Booking.start < booking.end,
        app.models.Booking.end > booking.start
    ).first()

    if overlap_bookings:
        return None, "overlap"

    # create booking inside transaction
    new_booking = app.models.Booking(
        booking_id=booking.booking_id,
        resource_id=booking.resource_id,
        start=booking.start,
        end=booking.end,
        user_id=booking.user_id
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking, "created"



### Get bookings
def get_bookings_by_date(db: Session, resource_id: str, date_str: str):

    # date string to datetime 
    date = datetime.strptime(date_str, "%Y-%m-%d")
    day_start = date
    day_end = date + timedelta(days=1)

    bookings = db.query(app.models.Booking).filter(
        app.models.Booking.resource_id == resource_id,
        app.models.Booking.start < day_end,
        app.models.Booking.end > day_start
    ).all()

    return bookings

### delete bookings
def delete_booking(db, booking_id: str):
    booking = db.query(app.models.Booking).filter(
        app.models.Booking.booking_id == booking_id
    ).first()

    if booking:
        db.delete(booking)
        db.commit()
        return True
    return False