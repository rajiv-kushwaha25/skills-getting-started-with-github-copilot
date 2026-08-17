"""
Pytest configuration and fixtures for FastAPI application tests.

This module provides:
- Fresh app instance per test (no cross-test contamination)
- Test client for making requests to the API
- Fixture to reset activities data between tests
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def test_client():
    """
    Provides a TestClient connected to the FastAPI application.
    
    This fixture creates a fresh test client for each test, ensuring
    that tests are isolated and independent.
    
    Yields:
        TestClient: A FastAPI test client for making requests to the API
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Resets the in-memory activities database before each test.
    
    This fixture runs automatically before every test (autouse=True)
    to ensure a clean slate. It restores the activities dictionary to
    its original state with default data.
    
    This prevents test cross-contamination and ensures each test
    starts with predictable data.
    
    Yields:
        None
    """
    # Store original activities state
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
        "Basketball": {
            "description": "Competitive basketball team and training",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis techniques and play matches",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["james@mergington.edu", "grace@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and visual arts",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["isabella@mergington.edu", "lucas@mergington.edu"]
        },
        "Music Ensemble": {
            "description": "Play instruments and perform in concerts",
            "schedule": "Tuesdays, 4:30 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["maya@mergington.edu", "noah@mergington.edu"]
        },
        "Debate Club": {
            "description": "Develop argumentation and public speaking skills",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["ethan@mergington.edu", "ava@mergington.edu"]
        },
        "Science Club": {
            "description": "Conduct experiments and explore STEM topics",
            "schedule": "Mondays and Fridays, 3:30 PM - 4:30 PM",
            "max_participants": 24,
            "participants": ["mia@mergington.edu", "ryan@mergington.edu"]
        }
    }
    
    # Clear current activities and restore original state
    activities.clear()
    activities.update(original_activities)
    
    # Yield control to the test
    yield
    
    # Clean up (reset again after test, though next fixture will do this)
    activities.clear()
    activities.update(original_activities)
