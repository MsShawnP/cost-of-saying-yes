"""Demo golden-file lock + velocity-label regression for cost-of-saying-yes.

Locks the canonical Cinderhaven Walmart scenario so the deployed demo numbers
cannot drift during the client-mode conversion, and asserts the velocity input
label reads per-SKU-per-door (07-31 audit P2 — the model multiplies doors x SKUs
x velocity, so velocity is per SKU per door, and the label must say so).
"""

from pathlib import Path

from model.calculator import calculate_breakeven_velocity, calculate_scenario
from conftest import CINDERHAVEN_INPUTS


class TestDemoGolden:
    def test_realistic_summary_is_locked(self):
        r = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert r.summary == {
            "gross_revenue_year1": 499200.0,
            "total_deductions_year1": -103584.0,
            "net_revenue_year1": 395616.0,
            "upfront_investment": -134400.0,
            "cogs_year1": -224640.0,
            "ops_overhead_year1": -38784.0,
            "uncollected_at_year_end": -34112.0,
            "net_cash_impact_year1": -36320.0,
            "break_even_month": None,
            "broker_projection_year1": 499200,
        }

    def test_trough_is_locked(self):
        r = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert r.trough_value == -156352.0
        assert r.trough_month == 1

    def test_breakeven_velocity_is_locked(self):
        be = calculate_breakeven_velocity(
            retailer="walmart", doors=1200, skus=4, unit_price_wholesale=1.00,
            cogs_per_unit=0.45, broker_projection_year1=499_200, scenario="realistic",
        )
        assert be == 2.54


class TestVelocityLabelRegression:
    """07-31 P2: the velocity input must be labeled per-SKU-per-door."""

    def test_velocity_label_says_per_sku_per_door(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        # label text must make clear velocity is per SKU AND per door
        assert "units / SKU / door / week" in html
        # and the model genuinely multiplies by both doors and skus
        src = Path("model/calculator.py").read_text(encoding="utf-8")
        assert "doors * skus * velocity" in src
