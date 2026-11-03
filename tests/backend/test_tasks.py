"""
Tests for task API endpoints.
"""
import pytest

NEW_TASK = {"title": "Review shortages", "priority": "high", "dueDate": "2025-12-01"}


@pytest.mark.usefixtures("clean_tasks")
class TestTaskEndpoints:
    """Test suite for task-related endpoints."""

    def test_get_tasks_empty(self, client):
        """Test getting tasks when none exist."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task returns it as pending with a generated ID."""
        response = client.post("/api/tasks", json=NEW_TASK)
        assert response.status_code == 201

        data = response.json()
        assert data["id"]
        assert data["title"] == "Review shortages"
        assert data["priority"] == "high"
        assert data["dueDate"] == "2025-12-01"
        assert data["status"] == "pending"

    def test_create_task_trims_title(self, client):
        """Test surrounding whitespace is stripped from the title."""
        response = client.post("/api/tasks", json={**NEW_TASK, "title": "  Call supplier  "})
        assert response.status_code == 201
        assert response.json()["title"] == "Call supplier"

    def test_create_task_defaults_priority(self, client):
        """Test priority defaults to medium when omitted."""
        response = client.post("/api/tasks", json={"title": "No priority", "dueDate": "2025-12-01"})
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    def test_create_task_blank_title(self, client):
        """Test a whitespace-only title is rejected."""
        response = client.post("/api/tasks", json={**NEW_TASK, "title": "   "})
        assert response.status_code == 400

    def test_create_task_invalid_priority(self, client):
        """Test an unknown priority is rejected by validation."""
        response = client.post("/api/tasks", json={**NEW_TASK, "priority": "urgent"})
        assert response.status_code == 422

    def test_create_task_missing_due_date(self, client):
        """Test dueDate is required."""
        response = client.post("/api/tasks", json={"title": "No date"})
        assert response.status_code == 422

    def test_get_tasks_newest_first(self, client):
        """Test tasks are listed newest first."""
        client.post("/api/tasks", json={**NEW_TASK, "title": "first"})
        client.post("/api/tasks", json={**NEW_TASK, "title": "second"})

        titles = [t["title"] for t in client.get("/api/tasks").json()]
        assert titles == ["second", "first"]

    def test_task_ids_unique(self, client):
        """Test IDs are not reused, including after a delete."""
        first = client.post("/api/tasks", json=NEW_TASK).json()["id"]
        client.delete(f"/api/tasks/{first}")
        second = client.post("/api/tasks", json=NEW_TASK).json()["id"]
        assert first != second

    def test_toggle_task(self, client):
        """Test toggling flips between pending and completed."""
        task_id = client.post("/api/tasks", json=NEW_TASK).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.json()["status"] == "pending"

    def test_toggle_task_persists(self, client):
        """Test a toggled status is reflected in the task list."""
        task_id = client.post("/api/tasks", json=NEW_TASK).json()["id"]
        client.patch(f"/api/tasks/{task_id}")

        assert client.get("/api/tasks").json()[0]["status"] == "completed"

    def test_toggle_task_not_found(self, client):
        """Test toggling a missing task returns 404."""
        response = client.patch("/api/tasks/nonexistent")
        assert response.status_code == 404

    def test_delete_task(self, client):
        """Test deleting a task removes it."""
        task_id = client.post("/api/tasks", json=NEW_TASK).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_delete_task_not_found(self, client):
        """Test deleting a missing task returns 404."""
        response = client.delete("/api/tasks/nonexistent")
        assert response.status_code == 404
