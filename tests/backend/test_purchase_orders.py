"""
Tests for purchase order API endpoints.
"""
import pytest

NEW_PO = {
    "backlog_item_id": "1",
    "supplier_name": "Acme Supply Co",
    "quantity": 350,
    "unit_cost": 12.5,
    "expected_delivery_date": "2025-12-15",
    "notes": "Rush order",
}


@pytest.mark.usefixtures("clean_purchase_orders")
class TestPurchaseOrderEndpoints:
    """Test suite for purchase-order-related endpoints."""

    def test_create_purchase_order(self, client):
        """Test creating a purchase order returns it as Pending with a generated ID."""
        response = client.post("/api/purchase-orders", json=NEW_PO)
        assert response.status_code == 201

        data = response.json()
        assert data["id"].startswith("PO-")
        assert data["backlog_item_id"] == "1"
        assert data["supplier_name"] == "Acme Supply Co"
        assert data["quantity"] == 350
        assert data["unit_cost"] == 12.5
        assert data["status"] == "Pending"
        assert data["created_date"]
        assert data["notes"] == "Rush order"

    def test_create_purchase_order_without_notes(self, client):
        """Test notes are optional."""
        payload = {k: v for k, v in NEW_PO.items() if k != "notes"}
        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 201
        assert response.json()["notes"] is None

    def test_create_purchase_order_unknown_backlog_item(self, client):
        """Test a missing backlog item returns 404."""
        response = client.post("/api/purchase-orders", json={**NEW_PO, "backlog_item_id": "does-not-exist"})
        assert response.status_code == 404

    def test_create_purchase_order_duplicate(self, client):
        """Test a second PO for the same backlog item is rejected."""
        client.post("/api/purchase-orders", json=NEW_PO)
        response = client.post("/api/purchase-orders", json=NEW_PO)
        assert response.status_code == 409

    @pytest.mark.parametrize("override", [
        {"quantity": 0},
        {"quantity": -5},
        {"unit_cost": -1},
        {"supplier_name": "   "},
    ])
    def test_create_purchase_order_invalid_values(self, client, override):
        """Test invalid quantity, cost or supplier is rejected."""
        response = client.post("/api/purchase-orders", json={**NEW_PO, **override})
        assert response.status_code == 400

    def test_create_purchase_order_missing_fields(self, client):
        """Test required fields are enforced by validation."""
        response = client.post("/api/purchase-orders", json={"backlog_item_id": "1"})
        assert response.status_code == 422

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test fetching a PO by its backlog item ID."""
        created = client.post("/api/purchase-orders", json=NEW_PO).json()

        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_purchase_order_not_found(self, client):
        """Test a backlog item without a PO returns 404."""
        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 404

    def test_backlog_reflects_purchase_order(self, client):
        """Test the backlog list exposes the PO so the dashboard shows 'View PO' after a reload."""
        before = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert before["1"]["has_purchase_order"] is False
        assert before["1"]["purchase_order_id"] is None

        po_id = client.post("/api/purchase-orders", json=NEW_PO).json()["id"]

        after = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert after["1"]["has_purchase_order"] is True
        assert after["1"]["purchase_order_id"] == po_id
        assert after["2"]["purchase_order_id"] is None
