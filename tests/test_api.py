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

    def test_costco_retailer_accepted(self):
        """costco is a valid retailer key and must return 200 with valid cash flow."""
        payload = {**VALID_PAYLOAD, "retailer": "costco"}
        response = client.post("/api/calculate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["realistic"]["cumulative_cash_position"]) == 12

    def test_regional_chain_retailer_accepted(self):
        """regional_chain is a valid retailer key and must return 200 with valid cash flow."""
        payload = {**VALID_PAYLOAD, "retailer": "regional_chain"}
        response = client.post("/api/calculate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["realistic"]["cumulative_cash_position"]) == 12


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
# POST /api/download/excel
# ---------------------------------------------------------------------------

class TestDownloadExcelEndpoint:

    def test_returns_200(self):
        response = client.post("/api/download/excel", json=VALID_PAYLOAD)
        assert response.status_code == 200

    def test_content_type_is_xlsx(self):
        response = client.post("/api/download/excel", json=VALID_PAYLOAD)
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in response.headers["content-type"]
        )

    def test_content_disposition_is_attachment(self):
        response = client.post("/api/download/excel", json=VALID_PAYLOAD)
        cd = response.headers["content-disposition"]
        assert "attachment" in cd
        assert "retailer-launch-model.xlsx" in cd

    def test_invalid_retailer_returns_422(self):
        response = client.post("/api/download/excel", json={**VALID_PAYLOAD, "retailer": "target"})
        assert response.status_code == 422

    def test_costco_download_returns_200(self):
        """costco retailer must return a non-empty xlsx response."""
        response = client.post("/api/download/excel", json={**VALID_PAYLOAD, "retailer": "costco"})
        assert response.status_code == 200
        assert len(response.content) > 0

    def test_workbook_reflects_posted_inputs(self):
        """Returned workbook must use posted inputs, not hardcoded defaults."""
        import io
        import openpyxl

        # Summary B2 = realistic gross revenue year 1.
        # doors=600 must produce half the revenue of doors=1200.
        response_600  = client.post("/api/download/excel", json={**VALID_PAYLOAD, "doors": 600})
        response_1200 = client.post("/api/download/excel", json=VALID_PAYLOAD)
        assert response_600.status_code == 200
        assert response_1200.status_code == 200

        revenue_600  = openpyxl.load_workbook(io.BytesIO(response_600.content))["Summary"]["B2"].value
        revenue_1200 = openpyxl.load_workbook(io.BytesIO(response_1200.content))["Summary"]["B2"].value
        assert revenue_600 < revenue_1200


# ---------------------------------------------------------------------------
# POST /api/compare
# ---------------------------------------------------------------------------

COMPARE_PAYLOAD = {k: v for k, v in VALID_PAYLOAD.items() if k != "retailer"}


class TestCompareEndpoint:

    def test_returns_200_with_four_retailers(self):
        """Valid payload returns 200 with retailers array of length 4."""
        response = client.post("/api/compare", json=COMPARE_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert len(data["retailers"]) == 4

    def test_each_entry_has_required_keys(self):
        """Every retailer entry must have key, label, trough_value, trough_month, break_even_month, net_cash_impact_year1."""
        response = client.post("/api/compare", json=COMPARE_PAYLOAD)
        data = response.json()
        required = {"key", "label", "trough_value", "trough_month", "break_even_month", "net_cash_impact_year1"}
        for entry in data["retailers"]:
            assert required <= set(entry.keys()), f"Missing keys in {entry}"

    def test_result_sorted_best_to_worst(self):
        """Retailers must be sorted by net_cash_impact_year1 descending."""
        response = client.post("/api/compare", json=COMPARE_PAYLOAD)
        data = response.json()
        values = [r["net_cash_impact_year1"] for r in data["retailers"]]
        assert values == sorted(values, reverse=True)

    def test_doors_zero_returns_422(self):
        response = client.post("/api/compare", json={**COMPARE_PAYLOAD, "doors": 0})
        assert response.status_code == 422

    def test_cogs_greater_than_price_returns_422(self):
        response = client.post("/api/compare", json={**COMPARE_PAYLOAD, "cogs_per_unit": 1.50})
        assert response.status_code == 422

    def test_non_numeric_velocity_returns_422(self):
        response = client.post("/api/compare", json={**COMPARE_PAYLOAD, "velocity_units_per_door_per_week": "fast"})
        assert response.status_code == 422

    def test_all_four_retailer_keys_present(self):
        """Response must include walmart, whole_foods, costco, regional_chain."""
        response = client.post("/api/compare", json=COMPARE_PAYLOAD)
        data = response.json()
        keys = {r["key"] for r in data["retailers"]}
        assert keys == {"walmart", "whole_foods", "costco", "regional_chain"}


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_returns_200_with_ok_status(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
