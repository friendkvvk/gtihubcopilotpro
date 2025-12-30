"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    global activities
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
        },
        "Basketball": {
            "description": "Team basketball games and skill development",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"],
        },
    })


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_index(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert "Chess Club" in data
        assert "Basketball" in data
        assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"
        assert len(data["Chess Club"]["participants"]) == 2

    def test_get_activities_returns_correct_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up newstudent@mergington.edu for Chess Club" in response.json()["message"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_participant(self, client):
        """Test signing up a student who is already registered"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_adds_participant_to_list(self, client):
        """Test that signup actually adds participant to the list"""
        email = "newstudent@mergington.edu"
        client.post("/activities/Basketball/signup", params={"email": email})
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Basketball"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Removed michael@mergington.edu from Chess Club" in response.json()["message"]

    def test_remove_participant_activity_not_found(self, client):
        """Test removing participant from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/participants",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_remove_participant_not_registered(self, client):
        """Test removing a participant who is not registered"""
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Student not registered for this activity"

    def test_remove_participant_actually_removes_from_list(self, client):
        """Test that removal actually removes participant from the list"""
        email = "michael@mergington.edu"
        client.delete("/activities/Chess Club/participants", params={"email": email})
        
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]


class TestWorkflow:
    """Integration tests for complete workflows"""

    def test_signup_and_remove_workflow(self, client):
        """Test complete workflow of signing up and removing a participant"""
        email = "workflow@mergington.edu"
        activity = "Basketball"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify participant is in the list
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]
        
        # Remove participant
        remove_response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        assert remove_response.status_code == 200
        
        # Verify participant is removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]
