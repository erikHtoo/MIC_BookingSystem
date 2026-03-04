# schemas.py {
#     - Pydantic models (request/response validation)
# }

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class BookingCreate(BaseModel):
    booking_id: str = Field(..., min_length=1)
    resource_id: str = Field(..., min_length=1)
    start: datetime
    end: datetime
    user_id: str = Field(..., min_length=1)


class Booking(BaseModel):
    booking_id: str
    resource_id: str
    start: datetime
    end: datetime
    user_id: str

    model_config = ConfigDict(from_attributes=True)