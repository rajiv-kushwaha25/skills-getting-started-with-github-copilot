"""
Unit tests for FastAPI activity management endpoints.

Tests cover individual endpoint functionality using the AAA (Arrange-Act-Assert) pattern:
- GET /activities: Retrieve list of all activities
- GET /: Redirect to static HTML
- POST /activities/{name}/signup: Register a student for an activity
- DELETE /activities/{name}/participants/{email}: Remove a participant from an activity
"""

import pytest
from fastapi.testclient import TestClient


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_html(self, test_client):
        """
        ARRANGE: Test client ready
        ACT: GET /
        ASSERT: Redirects to /static/index.html
        """
        # ACT
        response = test_client.get("/", follow_redirects=False)
        
        # ASSERT
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities_returns_200(self, test_client):
        """
        ARRANGE: Test client ready
        ACT: GET /activities
        ASSERT: Status 200 and response is dict
        """
        # ACT
        response = test_client.get("/activities")
        
        # ASSERT
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_all_activity_names(self, test_client):
        """
        ARRANGE: Expected activity names
        ACT: GET /activities
        ASSERT: All expected activities present in response
        """
        # ARRANGE
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball",
            "Tennis Club",
            "Art Studio",
            "Music Ensemble",
            "Debate Club",
            "Science Club",
        ]
        
        # ACT
        response = test_client.get("/activities")
        activities = response.json()
        
        # ASSERT
        for activity_name in expected_activities:
            assert activity_name in activities

    def test_activity_has_required_fields(self, test_client):
        """
        ARRANGE: Test client ready
        ACT: GET /activities
        ASSERT: Each activity has description, schedule, max_participants, participants
        """
        # ARRANGE
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # ACT
        response = test_client.get("/activities")
        activities = response.json()
        
        # ASSERT
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"{activity_name} missing {field}"

    def test_participants_is_list(self, test_client):
        """
        ARRANGE: Test client ready
        ACT: GET /activities
        ASSERT: participants field is a list for each activity
        """
        # ACT
        response = test_client.get("/activities")
        activities = response.json()
        
        # ASSERT
        for activity_name, activity_data in activities.items():
            assert isinstance(
                activity_data["participants"], list
            ), f"{activity_name} participants not a list"

    def test_activities_have_default_participants(self, test_client):
        """
        ARRANGE: Test client ready
        ACT: GET /activities
        ASSERT: Some activities have pre-registered participants
        """
        # ACT
        response = test_client.get("/activities")
        activities = response.json()
        
        # ASSERT
        # Chess Club should have 2 participants by default
        assert len(activities["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, test_client):
        """
        ARRANGE: New email address for an activity
        ACT: POST signup request
        ASSERT: Status 200 and success message returned
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # ACT
        response = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # ASSERT
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]

    def test_signup_adds_participant_to_activity(self, test_client):
        """
        ARRANGE: New email address
        ACT: POST signup, then GET activities
        ASSERT: Participant appears in activity's participants list
        """
        # ARRANGE
        activity_name = "Programming Class"
        email = "newcomer@mergington.edu"
        
        # ACT: Sign up
        test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # ACT: Fetch activities
        response = test_client.get("/activities")
        activities = response.json()
        
        # ASSERT
        assert email in activities[activity_name]["participants"]

    def test_signup_duplicate_email_returns_400(self, test_client):
        """
        ARRANGE: Email already registered for activity
        ACT: POST signup with same email again
        ASSERT: Status 400 and error message
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # ACT
        response = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # ASSERT
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, test_client):
        """
        ARRANGE: Activity that doesn't exist
        ACT: POST signup for non-existent activity
        ASSERT: Status 404 and error message
        """
        # ARRANGE
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # ACT
        response = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # ASSERT
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_different_email_same_activity_succeeds(self, test_client):
        """
        ARRANGE: Two different emails for same activity
        ACT: POST signup for both
        ASSERT: Both successful, both added to participants
        """
        # ARRANGE
        activity_name = "Tennis Club"
        email1 = "player1@mergington.edu"
        email2 = "player2@mergington.edu"
        
        # ACT: Sign up first student
        response1 = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        
        # ACT: Sign up second student
        response2 = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        
        # ASSERT: Both succeeded
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # ASSERT: Both in participants list
        activities = test_client.get("/activities").json()
        assert email1 in activities[activity_name]["participants"]
        assert email2 in activities[activity_name]["participants"]

    def test_signup_same_email_different_activity_succeeds(self, test_client):
        """
        ARRANGE: Same email for two different activities
        ACT: POST signup for both
        ASSERT: Both successful, email in both activities
        """
        # ARRANGE
        email = "versatile@mergington.edu"
        activity1 = "Art Studio"
        activity2 = "Music Ensemble"
        
        # ACT: Sign up for first activity
        response1 = test_client.post(
            f"/activities/{activity1}/signup",
            params={"email": email}
        )
        
        # ACT: Sign up for second activity
        response2 = test_client.post(
            f"/activities/{activity2}/signup",
            params={"email": email}
        )
        
        # ASSERT: Both succeeded
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # ASSERT: Email in both activities
        activities = test_client.get("/activities").json()
        assert email in activities[activity1]["participants"]
        assert email in activities[activity2]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint."""

    def test_remove_participant_success(self, test_client):
        """
        ARRANGE: Existing participant in an activity
        ACT: DELETE request for that participant
        ASSERT: Status 200 and success message
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Known participant
        
        # ACT
        response = test_client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # ASSERT
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]

    def test_remove_participant_removes_from_list(self, test_client):
        """
        ARRANGE: Participant in activity
        ACT: DELETE request, then GET activities
        ASSERT: Participant no longer in list
        """
        # ARRANGE
        activity_name = "Programming Class"
        email = "emma@mergington.edu"
        
        # Verify participant exists
        activities = test_client.get("/activities").json()
        assert email in activities[activity_name]["participants"]
        
        # ACT: Remove participant
        test_client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # ACT: Get updated activities
        activities = test_client.get("/activities").json()
        
        # ASSERT: Participant removed
        assert email not in activities[activity_name]["participants"]

    def test_remove_nonexistent_participant_returns_404(self, test_client):
        """
        ARRANGE: Email not in activity's participants
        ACT: DELETE request for non-existent participant
        ASSERT: Status 404 and error message
        """
        # ARRANGE
        activity_name = "Gym Class"
        email = "nothere@mergington.edu"
        
        # ACT
        response = test_client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # ASSERT
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_remove_from_nonexistent_activity_returns_404(self, test_client):
        """
        ARRANGE: Activity that doesn't exist
        ACT: DELETE request for participant in non-existent activity
        ASSERT: Status 404 and error message
        """
        # ARRANGE
        activity_name = "Fake Activity"
        email = "student@mergington.edu"
        
        # ACT
        response = test_client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # ASSERT
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_remove_participant_not_affects_other_activities(self, test_client):
        """
        ARRANGE: Participant in multiple activities
        ACT: Remove from one activity
        ASSERT: Still in other activities
        """
        # ARRANGE: Sign up same email for two activities
        email = "busy@mergington.edu"
        activity1 = "Debate Club"
        activity2 = "Science Club"
        
        test_client.post(f"/activities/{activity1}/signup", params={"email": email})
        test_client.post(f"/activities/{activity2}/signup", params={"email": email})
        
        # ACT: Remove from one activity
        test_client.delete(f"/activities/{activity1}/participants/{email}")
        
        # ACT: Check activities
        activities = test_client.get("/activities").json()
        
        # ASSERT: Removed from activity1, still in activity2
        assert email not in activities[activity1]["participants"]
        assert email in activities[activity2]["participants"]
