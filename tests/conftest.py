"""Pytest configuration and fixtures for FastAPI backend tests."""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient instance for making HTTP requests to the app."""
    return TestClient(app)


@pytest.fixture
def reset_activities(monkeypatch):
    """Reset the in-memory activities database to a clean state before each test."""
    # Store original activities
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Cricket": {
            "description": "Team sport focusing on batting, bowling, and fielding skills",
            "schedule": "Wednesdays and Saturdays, 4:00 PM - 6:00 PM",
            "max_participants": 22,
            "participants": ["liam@mergington.edu", "maya@mergington.edu"]
        }
    }

    # Replace the activities dict with clean state
    monkeypatch.setattr("src.app.activities", original_activities)
    
    yield
    
    # Restore original activities after test (cleanup)
    monkeypatch.setattr("src.app.activities", original_activities)
