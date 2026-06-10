"""Comprehensive tests for Mergington High School Activities API.

Tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and conditions
- Act: Execute the code being tested
- Assert: Verify the results
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities."""
        # Arrange
        # (no setup needed - using fixture defaults)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Cricket" in data

    def test_get_activities_response_structure(self, client, reset_activities):
        """Test that each activity has the correct structure."""
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            for field in expected_fields:
                assert field in activity_data, f"{field} missing from {activity_name}"
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_has_cache_control_header(self, client, reset_activities):
        """Test that GET /activities includes Cache-Control: no-store header."""
        # Arrange
        expected_cache_control = "no-store"

        # Act
        response = client.get("/activities")

        # Assert
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == expected_cache_control

    def test_get_activities_participants_populated(self, client, reset_activities):
        """Test that activities have initial participants."""
        # Arrange
        activity_name = "Chess Club"
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert len(data[activity_name]["participants"]) == 2
        for participant in expected_participants:
            assert participant in data[activity_name]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """Test that GET / redirects to /static/index.html."""
        # Arrange
        expected_status_code = 307
        expected_location = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == expected_status_code
        assert response.headers["location"] == expected_location


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_adds_participant_to_list(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity."""
        # Arrange
        activity_name = "Programming Class"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]

    def test_signup_has_cache_control_header(self, client, reset_activities):
        """Test that signup response includes Cache-Control: no-store header."""
        # Arrange
        activity_name = "Chess Club"
        email = "test@mergington.edu"
        expected_cache_control = "no-store"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == expected_cache_control

    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity returns 404."""
        # Arrange
        activity_name = "NonExistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that signup fails if student is already signed up."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_activity_at_capacity(self, client, reset_activities):
        """Test signup fails when activity is at max capacity."""
        # Arrange
        activity_name = "Gym Class"
        max_participants = 30
        current_participants = 2
        slots_to_fill = max_participants - current_participants

        # Act - Fill up the activity to capacity
        for i in range(slots_to_fill):
            email = f"student{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Now try to add one more - should fail
        overflow_email = "overflow@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": overflow_email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "capacity" in data["detail"].lower()

    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test that same student can signup for multiple different activities."""
        # Arrange
        email = "multiactivity@mergington.edu"
        activity_1 = "Chess Club"
        activity_2 = "Programming Class"

        # Act - Sign up for first activity
        response1 = client.post(
            f"/activities/{activity_1}/signup",
            params={"email": email}
        )
        
        # Sign up for second activity
        response2 = client.post(
            f"/activities/{activity_2}/signup",
            params={"email": email}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both signups worked
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_1]["participants"]
        assert email in activities_data[activity_2]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Verify email is signed up
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity_name]["participants"]

    def test_unregister_only_removes_target_participant(self, client, reset_activities):
        """Test that unregister only removes the specified email."""
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"
        
        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email_to_remove}
        )

        # Assert
        assert response.status_code == 200
        
        # Verify only one was removed and the other remains
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data[activity_name]["participants"]
        
        assert email_to_remove not in participants
        assert email_to_keep in participants
        assert len(participants) == initial_count - 1

    def test_unregister_has_cache_control_header(self, client, reset_activities):
        """Test that unregister response includes Cache-Control: no-store header."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        expected_cache_control = "no-store"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == expected_cache_control

    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister for non-existent activity returns 404."""
        # Arrange
        activity_name = "NonExistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_student_not_signed_up(self, client, reset_activities):
        """Test unregister fails if student is not signed up."""
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_signup_then_unregister_frees_capacity(self, client, reset_activities):
        """Test that unregistering frees up capacity for new signups."""
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        new_email = "newstudent@mergington.edu"

        # Act - Remove an existing participant
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email_to_remove}
        )
        assert response.status_code == 200

        # Now signup with the new email
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        
        # Verify the new participant is in the list
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert new_email in activities_data[activity_name]["participants"]
        assert email_to_remove not in activities_data[activity_name]["participants"]
