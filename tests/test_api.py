"""HTTP integration tests for the FastAPI endpoints.

Uses FastAPI's TestClient (wraps httpx) to exercise the full request/response
pipeline including Pydantic validation, calculator, and StreamingResponse —
without spinning up a real server.
"""

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

VALID_PAYLOAD = {
    "retailer": "walmart",
    "doors": 1200,
    "skus": 4,
    "unit_price_wholesale": 1.00,
    "cogs_per_unit": 0.45,
    "velocity_units_per_door_per_week": 2.0,
    "broker_projection_year1": 499_200,
}


# ---------------------------------------------------------------------------
# POST /api/calculate — happy paths
# ---------------------------------------------------------------------------

class TestCalculateEndpoint:

    def test_returns_200_with_three_scenario_keys(self):
        """Valid payload must return 200 with all three scenario results."""
        response = client.post("/api/calculate", json=VALID_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"realistic", "optimistic", "pessimistic"}

    def test_each_scenario_has_12_month_cumulative(self):
        """Every scenario's cumulative_cash_position must be a 12-element list."""
        response = client.post("/api/calculate", json=VALID_PAYLOAD)
        data = response.json()
        for scenario in ("realistic", "optimistic", "pessimistic"):
            assert len(data[scenario]["cumulative_cash_position"]) == 12, (
                f"Expected 12 months in {scenario}, "
                f"got {len(data[scenario]['cumulative_cash_position'])}"
            )

    def test_omitting_broker_projection_returns_200(self):
        """broker_projection_year1 is optional — omitting it must not cause a 422."""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "broker_projection_year1"}
        response = client.post("/api/calculate", json=payload)
        assert response.status_code == 200

    def test_whole_foods_retailer_accepted(self):
        """whole_foods is a valid retailer key and must return 200."""
        payload = {**VALID_PAYLOAD, "retailer": "whole_foods"}
        response = client.post("/api/calculate", json=payload)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/calculate — validation rejections
# ---------------------------------------------------------------------------

class TestCalculateValidation:

    def test_doors_zero_returns_422(self):
        """doors=0 must be rejected by Pydantic validation."""
        response = client.post("/api/calculate", json={**VALID_PAYLOAD, "doors": 0})
        assert response.status_code == 422

    def test_cogs_greater_than_price_returns_422(self):
        """COGS >= wholesale price must be rejected."""
        response = client.post(
            "/api/calculate",
            json={**VALID_PAYLOAD, "cogs_per_unit": 1.50},
        )
        assert response.status_code == 422

    def test_invalid_retailer_returns_422(self):
        """An unknown retailer key must be rejected."""
        response = client.post(
            "/api/calculate",
            json={**VALID_PAYLOAD, "retailer": "target"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/download/excel
# ---------------------------------------------------------------------------

class TestDownloadExcelEndpoint:

    def test_returns_200(self):
        response = client.get("/api/download/excel")
        assert response.status_code == 200

    def test_content_type_is_xlsx(self):
        response = client.get("/api/download/excel")
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in response.headers["content-type"]
        )

    def test_content_disposition_is_attachment(self):
        response = client.get("/api/download/excel")
        cd = response.headers["content-disposition"]
        assert "attachment" in cd
        assert "retailer-launch-model.xlsx" in cd

    def test_invalid_retailer_returns_422(self):
        response = client.get("/api/download/excel?retailer=target")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_returns_200_with_ok_status(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
