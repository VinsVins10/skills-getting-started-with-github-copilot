"""Comprehensive tests for Mergington High School Activities API."""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 4
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Cricket" in data

    def test_get_activities_response_structure(self, client, reset_activities):
        """Test that each activity has the correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_has_cache_control_header(self, client, reset_activities):
        """Test that GET /activities includes Cache-Control: no-store header."""
        response = client.get("/activities")
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "no-store"

    def test_get_activities_participants_populated(self, client, reset_activities):
        """Test that activities have initial participants."""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have initial participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """Test that GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant_to_list(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity."""
        email = "newstudent@mergington.edu"
        
        # Signup
        response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Programming Class"]["participants"]

    def test_signup_has_cache_control_header(self, client, reset_activities):
        """Test that signup response includes Cache-Control: no-store header."""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "test@mergington.edu"}
        )
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "no-store"

    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity returns 404."""
        response = client.post(
            "/activities/NonExistent%20Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that signup fails if student is already signed up."""
        # Try to signup with an email that's already in Chess Club
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_activity_at_capacity(self, client, reset_activities):
        """Test signup fails when activity is at max capacity."""
        # Fill up Gym Class to capacity (currently has 2 participants, max is 30)
        # This test would need adjustment based on actual capacity
        # For now, we'll test with a smaller subset scenario
        
        # Get current state
        response = client.get("/activities")
        activities_data = response.json()
        
        # Gym Class has max_participants=30, participants=2
        # We need to fill it up to capacity
        for i in range(28):  # Add 28 more to reach 30
            email = f"student{i}@mergington.edu"
            response = client.post(
                "/activities/Gym%20Class/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Now try to add one more - should fail
        response = client.post(
            "/activities/Gym%20Class/signup",
            params={"email": "overflow@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "capacity" in data["detail"].lower() or "full" in data["detail"].lower()

    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test that same student can signup for multiple different activities."""
        email = "multiactivity@mergington.edu"
        
        # Signup for Chess Club
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Signup for Programming Class
        response2 = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups worked
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        email = "michael@mergington.edu"
        
        # Verify email is signed up
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        response = client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant."""
        email = "michael@mergington.edu"
        
        # Unregister
        response = client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Chess Club"]["participants"]

    def test_unregister_only_removes_target_participant(self, client, reset_activities):
        """Test that unregister only removes the specified email."""
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"
        
        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Unregister one
        response = client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": email_to_remove}
        )
        assert response.status_code == 200
        
        # Verify only one was removed and the other remains
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data["Chess Club"]["participants"]
        
        assert email_to_remove not in participants
        assert email_to_keep in participants
        assert len(participants) == initial_count - 1

    def test_unregister_has_cache_control_header(self, client, reset_activities):
        """Test that unregister response includes Cache-Control: no-store header."""
        response = client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "no-store"

    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister for non-existent activity returns 404."""
        response = client.delete(
            "/activities/NonExistent%20Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_student_not_signed_up(self, client, reset_activities):
        """Test unregister fails if student is not signed up."""
        response = client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_signup_then_unregister_frees_capacity(self, client, reset_activities):
        """Test that unregistering frees up capacity for new signups."""
        email_to_remove = "michael@mergington.edu"
        new_email = "newstudent@mergington.edu"
        
        # Remove an existing participant
        response = client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": email_to_remove}
        )
        assert response.status_code == 200
        
        # Now signup with the new email should succeed
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": new_email}
        )
        assert response.status_code == 200
        
        # Verify the new participant is in the list
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert new_email in activities_data["Chess Club"]["participants"]
        assert email_to_remove not in activities_data["Chess Club"]["participants"]
