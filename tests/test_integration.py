"""
Integration tests for FastAPI activity management workflows.

Tests cover complete user workflows using the AAA (Arrange-Act-Assert) pattern:
- Signup → Participant List Update
- Signup → Remove → List Update
- Multiple Signups → Availability Calculation
- Error Flows and Edge Cases
"""

import pytest
from fastapi.testclient import TestClient


class TestSignupIntegration:
    """Integration tests for signup workflows."""

    def test_signup_updates_availability_count(self, test_client):
        """
        ARRANGE: Activity with known max_participants and current participants
        ACT: Sign up new student
        ASSERT: Availability count decreases by 1
        """
        # ARRANGE
        activity = "Basketball"
        original = test_client.get("/activities").json()
        original_spots = (
            original[activity]["max_participants"] - len(original[activity]["participants"])
        )
        
        # ACT: Sign up new participant
        new_email = "recruit@mergington.edu"
        test_client.post(f"/activities/{activity}/signup", params={"email": new_email})
        
        # ASSERT: Spots decreased
        updated = test_client.get("/activities").json()
        new_spots = (
            updated[activity]["max_participants"] - len(updated[activity]["participants"])
        )
        assert new_spots == original_spots - 1

    def test_multiple_signups_all_appear_in_list(self, test_client):
        """
        ARRANGE: Three new emails
        ACT: Sign up all three for same activity
        ASSERT: All three appear in activity's participants list
        """
        # ARRANGE
        activity = "Art Studio"
        emails = [
            "artist1@mergington.edu",
            "artist2@mergington.edu",
            "artist3@mergington.edu",
        ]
        
        # ACT: Sign up all three
        for email in emails:
            response = test_client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # ASSERT: All in participants
        activities = test_client.get("/activities").json()
        for email in emails:
            assert email in activities[activity]["participants"]

    def test_signup_response_message_includes_email_and_activity(self, test_client):
        """
        ARRANGE: Email and activity name
        ACT: POST signup
        ASSERT: Response message contains both email and activity name
        """
        # ARRANGE
        activity = "Music Ensemble"
        email = "musician@mergington.edu"
        
        # ACT
        response = test_client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # ASSERT
        message = response.json()["message"]
        assert email in message
        assert activity in message


class TestRemovalIntegration:
    """Integration tests for participant removal workflows."""

    def test_signup_then_remove_workflow(self, test_client):
        """
        ARRANGE: Activity and new email
        ACT: Sign up → Remove → Check list
        ASSERT: Participant added, then removed, final list is correct
        """
        # ARRANGE
        activity = "Gym Class"
        email = "temporary@mergington.edu"
        original_participants = test_client.get("/activities").json()[activity]["participants"].copy()
        
        # ACT: Sign up
        signup_response = test_client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # ASSERT: Participant added
        after_signup = test_client.get("/activities").json()[activity]["participants"]
        assert email in after_signup
        
        # ACT: Remove
        remove_response = test_client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        assert remove_response.status_code == 200
        
        # ASSERT: Participant removed, list restored
        final_participants = test_client.get("/activities").json()[activity]["participants"]
        assert email not in final_participants
        assert final_participants == original_participants

    def test_remove_restores_availability_slot(self, test_client):
        """
        ARRANGE: Activity and new participant
        ACT: Sign up, check spots, remove, check spots
        ASSERT: Spots decrease after signup, increase after removal
        """
        # ARRANGE
        activity = "Tennis Club"
        email = "tennis_player@mergington.edu"
        
        # ARRANGE: Initial state
        initial = test_client.get("/activities").json()
        initial_spots = initial[activity]["max_participants"] - len(initial[activity]["participants"])
        
        # ACT: Sign up
        test_client.post(f"/activities/{activity}/signup", params={"email": email})
        after_signup = test_client.get("/activities").json()
        after_signup_spots = (
            after_signup[activity]["max_participants"] - len(after_signup[activity]["participants"])
        )
        
        # ASSERT: Spots decreased
        assert after_signup_spots == initial_spots - 1
        
        # ACT: Remove
        test_client.delete(f"/activities/{activity}/participants/{email}")
        after_removal = test_client.get("/activities").json()
        after_removal_spots = (
            after_removal[activity]["max_participants"] - len(after_removal[activity]["participants"])
        )
        
        # ASSERT: Spots restored
        assert after_removal_spots == initial_spots

    def test_remove_response_message_includes_email_and_activity(self, test_client):
        """
        ARRANGE: Existing participant
        ACT: DELETE request
        ASSERT: Response message contains both email and activity name
        """
        # ARRANGE
        activity = "Debate Club"
        email = "ethan@mergington.edu"
        
        # ACT
        response = test_client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        
        # ASSERT
        message = response.json()["message"]
        assert email in message
        assert activity in message


class TestComplexWorkflows:
    """Integration tests for complex multi-step workflows."""

    def test_signup_multiple_then_remove_one(self, test_client):
        """
        ARRANGE: Three new participants for one activity
        ACT: Sign up all three, remove one
        ASSERT: Other two remain
        """
        # ARRANGE
        activity = "Science Club"
        emails = [
            "scientist1@mergington.edu",
            "scientist2@mergington.edu",
            "scientist3@mergington.edu",
        ]
        
        # ACT: Sign up all
        for email in emails:
            test_client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # ASSERT: All present
        participants = test_client.get("/activities").json()[activity]["participants"]
        for email in emails:
            assert email in participants
        
        # ACT: Remove one
        test_client.delete(f"/activities/{activity}/participants/{emails[1]}")
        
        # ASSERT: One removed, two remain
        participants = test_client.get("/activities").json()[activity]["participants"]
        assert emails[0] in participants
        assert emails[1] not in participants
        assert emails[2] in participants

    def test_user_signup_remove_signup_again(self, test_client):
        """
        ARRANGE: Activity and email
        ACT: Sign up → Remove → Sign up again
        ASSERT: All operations succeed
        """
        # ARRANGE
        activity = "Chess Club"
        email = "player@mergington.edu"
        
        # ACT: Sign up
        signup1 = test_client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup1.status_code == 200
        
        # ACT: Remove
        remove = test_client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        assert remove.status_code == 200
        
        # ACT: Sign up again
        signup2 = test_client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup2.status_code == 200
        
        # ASSERT: Final state - email is registered
        participants = test_client.get("/activities").json()[activity]["participants"]
        assert email in participants

    def test_same_email_different_activities_independent_removal(self, test_client):
        """
        ARRANGE: One email registered for two activities
        ACT: Remove from one, check other
        ASSERT: Removal is activity-specific
        """
        # ARRANGE
        email = "multitasker@mergington.edu"
        activity1 = "Programming Class"
        activity2 = "Music Ensemble"
        
        # ACT: Sign up for both
        test_client.post(f"/activities/{activity1}/signup", params={"email": email})
        test_client.post(f"/activities/{activity2}/signup", params={"email": email})
        
        # ASSERT: In both
        activities = test_client.get("/activities").json()
        assert email in activities[activity1]["participants"]
        assert email in activities[activity2]["participants"]
        
        # ACT: Remove from activity1
        test_client.delete(f"/activities/{activity1}/participants/{email}")
        
        # ASSERT: Only removed from activity1
        activities = test_client.get("/activities").json()
        assert email not in activities[activity1]["participants"]
        assert email in activities[activity2]["participants"]


class TestErrorFlows:
    """Integration tests for error handling and edge cases."""

    def test_duplicate_signup_error_doesnt_add_participant(self, test_client):
        """
        ARRANGE: Known participant
        ACT: Attempt duplicate signup
        ASSERT: Error returned, participant list unchanged
        """
        # ARRANGE
        activity = "Art Studio"
        email = "isabella@mergington.edu"  # Already registered
        original = test_client.get("/activities").json()[activity]["participants"].copy()
        
        # ACT: Attempt duplicate
        response = test_client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # ASSERT: Error returned
        assert response.status_code == 400
        
        # ASSERT: List unchanged
        current = test_client.get("/activities").json()[activity]["participants"]
        assert current == original

    def test_delete_nonexistent_doesnt_affect_activity(self, test_client):
        """
        ARRANGE: Activity with known participants
        ACT: DELETE non-existent participant
        ASSERT: Error returned, participant list unchanged
        """
        # ARRANGE
        activity = "Basketball"
        email = "nobody@mergington.edu"
        original = test_client.get("/activities").json()[activity]["participants"].copy()
        
        # ACT: Try to delete non-existent
        response = test_client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        
        # ASSERT: Error returned
        assert response.status_code == 404
        
        # ASSERT: List unchanged
        current = test_client.get("/activities").json()[activity]["participants"]
        assert current == original

    def test_operations_on_nonexistent_activity(self, test_client):
        """
        ARRANGE: Non-existent activity name
        ACT: Try signup, try remove
        ASSERT: Both return 404
        """
        # ARRANGE
        fake_activity = "Nonexistent Activity XYZ"
        email = "test@mergington.edu"
        
        # ACT: Try signup
        signup_response = test_client.post(
            f"/activities/{fake_activity}/signup",
            params={"email": email}
        )
        
        # ASSERT: 404
        assert signup_response.status_code == 404
        
        # ACT: Try remove
        remove_response = test_client.delete(
            f"/activities/{fake_activity}/participants/{email}"
        )
        
        # ASSERT: 404
        assert remove_response.status_code == 404
