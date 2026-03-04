# models.py {
#     - SQLAlchemy database models
#     - Booking table definition
# }

from sqlalchemy import Column, String, DateTime, Index
from app.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, index=True, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    user_id = Column(String, nullable=False)

# composite index for faster overlap queries
Index("idx_resource_time", Booking.resource_id, Booking.start, Booking.end)