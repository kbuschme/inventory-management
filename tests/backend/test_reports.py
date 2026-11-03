"""
Tests for report API endpoints.
"""
import pytest

QUARTER_FIELDS = {"quarter", "total_orders", "total_revenue", "delivered_orders", "avg_order_value", "fulfillment_rate"}
MONTH_FIELDS = {"month", "order_count", "revenue", "delivered_count"}


class TestQuarterlyReports:
    """Test suite for /api/reports/quarterly."""

    def test_get_quarterly_reports(self, client):
        """Test the unfiltered report returns all four quarters in order with the model's fields."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert [q["quarter"] for q in data] == ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025"]
        assert all(set(q) == QUARTER_FIELDS for q in data)

    def test_quarterly_totals_match_orders(self, client):
        """Test the report covers every order exactly once."""
        orders = client.get("/api/orders").json()
        data = client.get("/api/reports/quarterly").json()

        assert sum(q["total_orders"] for q in data) == len(orders)
        assert sum(q["total_revenue"] for q in data) == pytest.approx(sum(o["total_value"] for o in orders), abs=0.05)

    def test_quarterly_derived_values(self, client):
        """Test the average and fulfillment rate are consistent with the counts."""
        for q in client.get("/api/reports/quarterly").json():
            assert q["avg_order_value"] == pytest.approx(q["total_revenue"] / q["total_orders"], abs=0.01)
            assert q["fulfillment_rate"] == pytest.approx(q["delivered_orders"] / q["total_orders"] * 100, abs=0.05)
            assert 0 <= q["fulfillment_rate"] <= 100

    def test_quarterly_respects_warehouse_filter(self, client):
        """Test the warehouse filter narrows the report to that warehouse's orders."""
        orders = client.get("/api/orders?warehouse=Tokyo").json()
        data = client.get("/api/reports/quarterly?warehouse=Tokyo").json()

        assert sum(q["total_orders"] for q in data) == len(orders)

    def test_quarterly_respects_category_filter(self, client):
        """Test the category filter narrows the report."""
        orders = client.get("/api/orders?category=Sensors").json()
        data = client.get("/api/reports/quarterly?category=Sensors").json()

        assert sum(q["total_orders"] for q in data) == len(orders)

    def test_quarterly_status_filter(self, client):
        """Test filtering to Delivered orders gives a 100% fulfillment rate in every quarter."""
        data = client.get("/api/reports/quarterly?status=Delivered").json()

        assert data
        assert all(q["fulfillment_rate"] == 100 for q in data)

    def test_quarterly_month_filter(self, client):
        """Test a single-month filter leaves only the quarter that month belongs to."""
        data = client.get("/api/reports/quarterly?month=2025-05").json()

        assert [q["quarter"] for q in data] == ["Q2-2025"]

    def test_quarterly_all_means_unfiltered(self, client):
        """Test 'all' is treated as no filter, as in the other endpoints."""
        unfiltered = client.get("/api/reports/quarterly").json()
        with_all = client.get("/api/reports/quarterly?warehouse=all&category=all&status=all&month=all").json()

        assert with_all == unfiltered

    def test_quarterly_no_matches(self, client):
        """Test filters that match nothing return an empty list, not an error."""
        response = client.get("/api/reports/quarterly?warehouse=Atlantis")
        assert response.status_code == 200
        assert response.json() == []


class TestMonthlyTrends:
    """Test suite for /api/reports/monthly-trends."""

    def test_get_monthly_trends(self, client):
        """Test the unfiltered report returns months in ascending order with the model's fields."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        months = [m["month"] for m in data]
        assert months == sorted(months)
        assert len(months) == len(set(months))
        assert all(set(m) == MONTH_FIELDS for m in data)

    def test_monthly_totals_match_orders(self, client):
        """Test the report covers every order exactly once."""
        orders = client.get("/api/orders").json()
        data = client.get("/api/reports/monthly-trends").json()

        assert sum(m["order_count"] for m in data) == len(orders)
        assert sum(m["revenue"] for m in data) == pytest.approx(sum(o["total_value"] for o in orders), abs=0.05)

    def test_monthly_revenue_is_rounded_to_cents(self, client):
        """Test revenue carries no accumulated floating-point noise."""
        for m in client.get("/api/reports/monthly-trends").json():
            assert m["revenue"] == round(m["revenue"], 2)

    def test_monthly_respects_filters(self, client):
        """Test warehouse and category filters narrow the monthly report."""
        orders = client.get("/api/orders?warehouse=London&category=Actuators").json()
        data = client.get("/api/reports/monthly-trends?warehouse=London&category=Actuators").json()

        assert sum(m["order_count"] for m in data) == len(orders)

    def test_monthly_month_filter(self, client):
        """Test a single-month filter returns just that month."""
        data = client.get("/api/reports/monthly-trends?month=2025-03").json()

        assert [m["month"] for m in data] == ["2025-03"]

    def test_monthly_quarter_filter(self, client):
        """Test a quarter filter returns that quarter's three months."""
        data = client.get("/api/reports/monthly-trends?month=Q3-2025").json()

        assert [m["month"] for m in data] == ["2025-07", "2025-08", "2025-09"]

    def test_monthly_delivered_count_never_exceeds_orders(self, client):
        """Test delivered orders are a subset of each month's orders."""
        for m in client.get("/api/reports/monthly-trends").json():
            assert 0 <= m["delivered_count"] <= m["order_count"]

    def test_monthly_no_matches(self, client):
        """Test filters that match nothing return an empty list."""
        response = client.get("/api/reports/monthly-trends?warehouse=Atlantis")
        assert response.status_code == 200
        assert response.json() == []
