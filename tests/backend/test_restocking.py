"""
Tests for restocking API endpoints.
"""
import pytest


@pytest.fixture
def restock_payload():
    """Restock order with two items whose lead times differ."""
    return {
        "items": [
            {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 10, "unit_cost": 100.0, "lead_time_days": 12},
            {"sku": "FLT-405", "name": "Oil Filter Cartridge", "quantity": 5, "unit_cost": 20.5, "lead_time_days": 7},
        ],
        "budget": 5000,
    }


@pytest.mark.usefixtures("clean_submitted_orders")
class TestRestockingEndpoints:
    """Test suite for restocking order endpoints."""

    def test_demand_forecasts_include_cost_and_lead_time(self, client):
        """Test that forecasts carry the fields restocking needs."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0
            assert isinstance(forecast["lead_time_days"], int)
            assert 7 <= forecast["lead_time_days"] <= 14

    def test_create_restock_order(self, client, restock_payload):
        """Test submitting a restocking order."""
        response = client.post("/api/restocking/orders", json=restock_payload)
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert len(order["items"]) == 2
        assert order["budget"] == 5000
        assert "T" in order["order_date"]
        assert "T" in order["expected_delivery"]

    def test_restock_order_total_calculation(self, client, restock_payload):
        """Test that the server computes the total from the items."""
        response = client.post("/api/restocking/orders", json=restock_payload)

        # 10 * 100.0 + 5 * 20.5
        assert abs(response.json()["total_value"] - 1102.5) < 0.01

    def test_restock_order_lead_time_is_slowest_item(self, client, restock_payload):
        """Test that the order lead time is the max item lead time."""
        response = client.post("/api/restocking/orders", json=restock_payload)
        assert response.json()["lead_time_days"] == 12

    def test_restock_order_rejects_empty_items(self, client):
        """Test that an order without items is rejected."""
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_restock_order_rejects_non_positive_quantity(self, client, restock_payload):
        """Test that zero or negative quantities are rejected."""
        restock_payload["items"][0]["quantity"] = 0
        response = client.post("/api/restocking/orders", json=restock_payload)
        assert response.status_code == 400

    def test_restock_order_rejects_missing_fields(self, client):
        """Test that Pydantic validation rejects malformed items."""
        response = client.post("/api/restocking/orders", json={"items": [{"sku": "WDG-001"}]})
        assert response.status_code == 422

    def test_get_restock_orders_empty(self, client):
        """Test listing when nothing has been submitted."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_restock_orders_newest_first(self, client, restock_payload):
        """Test that submitted orders are listed newest first."""
        first = client.post("/api/restocking/orders", json=restock_payload).json()
        second = client.post("/api/restocking/orders", json=restock_payload).json()
        assert first["id"] != second["id"]

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        data = response.json()
        assert [o["id"] for o in data] == [second["id"], first["id"]]

    def test_restock_orders_not_mixed_into_sales_orders(self, client, restock_payload):
        """Test that restocking orders stay out of the customer orders list."""
        before = len(client.get("/api/orders").json())
        client.post("/api/restocking/orders", json=restock_payload)
        after = len(client.get("/api/orders").json())
        assert before == after
