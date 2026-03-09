# main.py {
#     - Create FastAPI app
#     - Define API endpoints
#     - Call functions from crud.py 
#     }

from datetime import datetime, date, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, models, database

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

### POST /bookings

@app.post("/bookings", response_model=schemas.Booking)
def create_booking(
    booking: schemas.BookingCreate,
    response: Response,
    db: Session = Depends(database.get_db)
):
    try:
        result, state = crud.create_booking(db, booking)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if state == "exists":
        return result # already exists 

    if state == "overlap":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Booking overlaps with existing booking"
        )

    # created
    response.status_code = status.HTTP_201_CREATED
    return result

# GET /bookings?resource_id=...&date=...
@app.get("/bookings", response_model=List[schemas.Booking])
def get_bookings(
    resource_id: str = Query(...),
    date_str: date = Query(..., alias="date"),
    db: Session = Depends(database.get_db)
):

    bookings = crud.get_bookings_by_date(
    db,
    resource_id,
    date_str
)

    return bookings

# DELETE /bookings/{booking_id}
from fastapi import HTTPException

@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: str, db: Session = Depends(database.get_db)):
    deleted = crud.delete_booking(db, booking_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Booking not found")

    return {"message": "Booking deleted"}