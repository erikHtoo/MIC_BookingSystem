# automated tests

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base
import pytest


# function to reset test database before every test
@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
        
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency override
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# test 1: successful create (201)
def test_create_booking_success():
    response = client.post("/bookings", json={
        "booking_id": "test1",
        "resource_id": "room1",
        "start": "2026-03-03T10:00:00",
        "end": "2026-03-03T11:00:00",
        "user_id": "user1"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["booking_id"] == "test1"
    
# test 2: idempotency check with same booking id (200)
def test_idempotent_booking():
    payload = {
        "booking_id": "test2",
        "resource_id": "room2",
        "start": "2026-03-03T13:00:00",
        "end": "2026-03-03T14:00:00",
        "user_id": "user1"
    }

    first = client.post("/bookings", json=payload)
    second = client.post("/bookings", json=payload)

    # check status and response data
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json() == second.json()
    
# test 3: overlap (409)
def test_overlap_rejected():
    client.post("/bookings", json={
        "booking_id": "test3",
        "resource_id": "room2",
        "start": "2026-03-03T10:00:00",
        "end": "2026-03-03T11:00:00",
        "user_id": "user1"
    })

    overlap = client.post("/bookings", json={
        "booking_id": "test4",
        "resource_id": "room2",
        "start": "2026-03-03T10:30:00",
        "end": "2026-03-03T11:30:00",
        "user_id": "user2"
    })

    assert overlap.status_code == 409
    
# test 4: GET filtering 
def test_get_bookings_by_date():
    client.post("/bookings", json={
        "booking_id": "test5",
        "resource_id": "room3",
        "start": "2026-03-03T14:00:00",
        "end": "2026-03-03T15:00:00",
        "user_id": "user1"
    })

    response = client.get("/bookings", params={
        "resource_id": "room3",
        "date": "2026-03-03"
    })

    assert response.status_code == 200
    assert len(response.json()) >= 1

# test 5: delete success
def test_delete_booking_success():
    client.post("/bookings", json={
        "booking_id": "c5",
        "resource_id": "roomZ",
        "start": "2026-06-01T10:00:00",
        "end": "2026-06-01T11:00:00",
        "user_id": "user1"
    })

    response = client.delete("/bookings/c5")
    assert response.status_code == 200
    
# test 6: delete non-existent booking
def test_delete_booking_not_found():
    response = client.delete("/bookings/does_not_exist")
    assert response.status_code == 404
    
# test 7: concurrency test

import threading
def test_concurrent_overlapping_bookings():
    payload1 = {
        "booking_id": "concur1",
        "resource_id": "roomC",
        "start": "2026-07-01T10:00:00",
        "end": "2026-07-01T11:00:00",
        "user_id": "user1"
    }

    payload2 = {
        "booking_id": "concur2",
        "resource_id": "roomC",
        "start": "2026-07-01T10:30:00",
        "end": "2026-07-01T11:30:00",
        "user_id": "user2"
    }

    responses = []

    def create_booking(payload):
        response = client.post("/bookings", json=payload)
        responses.append(response.status_code)

    thread1 = threading.Thread(target=create_booking, args=(payload1,))
    thread2 = threading.Thread(target=create_booking, args=(payload2,))

    # start same time
    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    # One should succeed (201), one should fail (409)
    assert 201 in responses
    assert 409 in responses