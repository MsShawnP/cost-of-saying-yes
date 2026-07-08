"""Tests for the month-by-month cash flow model engine.

Critical invariant: cash_received[M] = net_invoiced[M - payment_lag_months].
Cash receipt is decoupled from invoice date — this is what creates the cash trough.
"""

import pytest
from pydantic import ValidationError
from model.calculator import calculate_scenario, calculate_all_scenarios
from model.defaults import RETAILER_DEFAULTS, SCENARIO_MULTIPLIERS
from app import ScenarioInput
from conftest import CINDERHAVEN_INPUTS


# ---------------------------------------------------------------------------
# Happy path — Cinderhaven realistic scenario
# ---------------------------------------------------------------------------

class TestCinderhavenRealistic:
    """The reference scenario — plug in Cinderhaven numbers and verify the shape."""

    def test_gross_revenue_within_1_percent(self):
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert abs(result.summary["gross_revenue_year1"] - 499_200) / 499_200 < 0.01

    def test_net_cash_impact_is_negative(self):
        """The whole point: year 1 is a cash loss, not a gain."""
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert result.summary["net_cash_impact_year1"] < 0

    def test_trough_is_deep_negative(self):
        """Trough should be deeply negative — this is the cash trough."""
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert result.trough_value < -100_000

    def test_months_array_is_1_through_12(self):
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert result.months == list(range(1, 13))

    def test_all_arrays_length_12(self):
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert len(result.gross_revenue) == 12
        assert len(result.cash_received) == 12
        assert len(result.deductions) == 12
        assert len(result.cumulative_cash_position) == 12

    def test_cumulative_cash_starts_negative(self):
        """Upfront costs mean the brand is immediately in the red."""
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert result.cumulative_cash_position[0] < 0


# ---------------------------------------------------------------------------
# Deduction lag — the critical invariant
# ---------------------------------------------------------------------------

class TestDeductionLag:
    """cash_received[M] must equal net_invoiced[M - payment_lag_months]."""

    def test_cash_received_month_1_is_zero(self):
        """With 2-month lag, no cash arrives in month 1."""
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert result.cash_received[0] == 0.0

    def test_cash_received_month_2_equals_net_invoiced_month_1(self):
        """With 1-month lag, cash arrives in month 2 (net_inv[0])."""
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        net_invoiced_0 = result.gross_revenue[0] - result.deductions[0]
        assert abs(result.cash_received[1] - net_invoiced_0) < 0.01

    def test_cash_received_month_3_equals_net_invoiced_month_2(self):
        """cash_received[2] must equal net_invoiced[1] for 1-month lag."""
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        net_invoiced_1 = result.gross_revenue[1] - result.deductions[1]
        assert abs(result.cash_received[2] - net_invoiced_1) < 0.01

    def test_cash_received_month_4_equals_net_invoiced_month_3(self):
        """Verify the lag holds for the third cash receipt too."""
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        net_invoiced_2 = result.gross_revenue[2] - result.deductions[2]
        assert abs(result.cash_received[3] - net_invoiced_2) < 0.01

    def test_whole_foods_cash_received_month_1_is_zero(self):
        """Whole Foods has 1-month lag — month 1 still zero."""
        inputs = {**CINDERHAVEN_INPUTS, "retailer": "whole_foods"}
        result = calculate_scenario(**inputs, scenario="realistic")
        assert result.cash_received[0] == 0.0

    def test_whole_foods_cash_received_month_2_equals_net_invoiced_month_1(self):
        """Whole Foods 1-month lag: cash_received[1] == net_invoiced[0]."""
        inputs = {**CINDERHAVEN_INPUTS, "retailer": "whole_foods"}
        result = calculate_scenario(**inputs, scenario="realistic")
        net_invoiced_0 = result.gross_revenue[0] - result.deductions[0]
        assert abs(result.cash_received[1] - net_invoiced_0) < 0.01


# ---------------------------------------------------------------------------
# Scenario ordering
# ---------------------------------------------------------------------------

class TestScenarioOrdering:
    """Optimistic > realistic > pessimistic on relevant metrics."""

    def setup_method(self):
        self.opt = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="optimistic")
        self.real = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        self.pess = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="pessimistic")

    def test_gross_revenue_ordering(self):
        assert (
            self.opt.summary["gross_revenue_year1"]
            > self.real.summary["gross_revenue_year1"]
            > self.pess.summary["gross_revenue_year1"]
        )

    def test_net_cash_impact_ordering(self):
        """Optimistic ends the year less negative (or more positive) than pessimistic."""
        assert (
            self.opt.summary["net_cash_impact_year1"]
            > self.real.summary["net_cash_impact_year1"]
            > self.pess.summary["net_cash_impact_year1"]
        )

    def test_trough_ordering(self):
        """Higher velocity means more COGS before cash arrives — optimistic trough
        is deeper (more negative) than pessimistic because higher monthly units
        are produced and paid for while cash is still in the lag window.
        The end-of-year net_cash_impact ordering is the opposite and is correct:
        optimistic recovers better, pessimistic stays deepest negative."""
        # Pessimistic trough is shallower (less negative) than optimistic
        assert self.pess.trough_value > self.real.trough_value > self.opt.trough_value

    def test_calculate_all_scenarios_returns_three_keys(self):
        results = calculate_all_scenarios(**CINDERHAVEN_INPUTS)
        assert set(results.keys()) == {"optimistic", "realistic", "pessimistic"}


# ---------------------------------------------------------------------------
# Break-even edge cases
# ---------------------------------------------------------------------------

class TestBreakEven:

    def test_very_low_velocity_break_even_is_none(self):
        """A brand that barely sells never recovers upfront costs."""
        inputs = {**CINDERHAVEN_INPUTS, "velocity_units_per_door_per_week": 0.1}
        result = calculate_scenario(**inputs, scenario="pessimistic")
        assert result.break_even_month is None

    def test_very_high_velocity_breaks_even(self):
        """Very high velocity with low upfront costs should break even."""
        inputs = {
            "retailer": "walmart",
            "doors": 100,          # fewer doors = lower upfront
            "skus": 1,
            "unit_price_wholesale": 5.00,
            "cogs_per_unit": 1.00,
            "velocity_units_per_door_per_week": 20.0,
            "broker_projection_year1": 100_000,
        }
        result = calculate_scenario(**inputs, scenario="optimistic")
        assert result.break_even_month is not None

    def test_break_even_month_is_positive_if_set(self):
        """break_even_month must be between 1 and 12 if not None.

        Uses high-velocity inputs that guarantee break_even_month is set so the
        inner assertion always runs. CINDERHAVEN_INPUTS+optimistic returns None
        (trough never recovers in 12 months) — that made this test vacuous.
        """
        result = calculate_scenario(
            retailer="walmart",
            doors=100,
            skus=1,
            unit_price_wholesale=5.00,
            cogs_per_unit=1.00,
            velocity_units_per_door_per_week=20.0,
            broker_projection_year1=100_000,
            scenario="optimistic",
        )
        assert result.break_even_month is not None, (
            "High-velocity fixture must have a break_even_month — check calculator logic"
        )
        assert 1 <= result.break_even_month <= 12

    def test_cumulative_cash_is_non_negative_at_break_even(self):
        """At break_even_month, cumulative cash position must be >= 0."""
        inputs = {
            "retailer": "walmart",
            "doors": 100,
            "skus": 1,
            "unit_price_wholesale": 5.00,
            "cogs_per_unit": 1.00,
            "velocity_units_per_door_per_week": 20.0,
            "broker_projection_year1": 100_000,
        }
        result = calculate_scenario(**inputs, scenario="optimistic")
        if result.break_even_month is not None:
            idx = result.break_even_month - 1
            assert result.cumulative_cash_position[idx] >= 0


# ---------------------------------------------------------------------------
# Cinderhaven validated pair regression — pins model to operator-confirmed numbers
# ---------------------------------------------------------------------------

class TestCinderhavenValidatedRegression:
    """Regression guard: Cinderhaven inputs must reproduce the operator-validated pair.

    Root cause of prior -$55K discrepancy (fixed 2026-06-01):
      - payment_lag_months was 2 (NET-60); validated operator uses NET-30 (lag=1)
      - ops_overhead_monthly was $2,000; validated figure implies $3,232/month

    If either parameter drifts, these tests catch it immediately.
    """

    def test_gross_revenue_matches_validated(self):
        from model.defaults import CINDERHAVEN_VALIDATED
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert result.summary["gross_revenue_year1"] == CINDERHAVEN_VALIDATED["gross_revenue_year1"]

    def test_net_cash_matches_validated(self):
        from model.defaults import CINDERHAVEN_VALIDATED
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert result.summary["net_cash_impact_year1"] == CINDERHAVEN_VALIDATED["net_cash_impact_year1"], (
            f"net_cash_impact mismatch: model={result.summary['net_cash_impact_year1']}, "
            f"validated={CINDERHAVEN_VALIDATED['net_cash_impact_year1']}"
        )

    def test_trough_value_matches_validated(self):
        """Pins the peak trough VALUE the case study prints (index.html) to the model."""
        from model.defaults import CINDERHAVEN_VALIDATED
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert result.trough_value == CINDERHAVEN_VALIDATED["peak_cash_trough"], (
            f"trough_value mismatch: model={result.trough_value}, "
            f"validated={CINDERHAVEN_VALIDATED['peak_cash_trough']}"
        )

    def test_trough_month_matches_validated(self):
        """Pins the peak trough MONTH. Prior copy claimed Month 4; the model puts it
        at Month 1 (upfront costs land pre-launch, first cash arrives Month 2)."""
        from model.defaults import CINDERHAVEN_VALIDATED
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        assert result.trough_month == CINDERHAVEN_VALIDATED["peak_cash_trough_month"], (
            f"trough_month mismatch: model={result.trough_month}, "
            f"validated={CINDERHAVEN_VALIDATED['peak_cash_trough_month']}"
        )
        assert result.trough_value == min(result.cumulative_cash_position)

    def test_year1_ending_position_is_mostly_reversing_receivable(self):
        """The -$36,320 year-1 ending position is ~94% timing: the Month-12 net
        invoice is collected in Month 13, outside the window. Backing it out, Year 1
        nets to roughly breakeven (-$2,208). Computed from the model, not asserted."""
        from model.defaults import CINDERHAVEN_VALIDATED
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        net = result.summary["net_cash_impact_year1"]
        # Month-12 net invoice (collected Month 13 under the 1-month lag) is the
        # receivable still outstanding at year end.
        outstanding = round(result.gross_revenue[11] - result.deductions[11], 2)
        assert outstanding == CINDERHAVEN_VALIDATED["outstanding_receivable_month12"]
        assert round(net + outstanding, 2) == CINDERHAVEN_VALIDATED["year1_pl_ex_timing"]
        # the reversing receivable is ~94% of the headline year-1 figure
        assert 0.90 < outstanding / abs(net) < 0.98

    def test_account_is_cash_positive_in_steady_state(self):
        """Once collections catch up (months 5-12), each month adds cash — the
        launch is a working-capital timing problem, not a P&L loss."""
        result = calculate_scenario(**CINDERHAVEN_INPUTS, scenario="realistic")
        cum = result.cumulative_cash_position
        monthly_deltas = [cum[m] - cum[m - 1] for m in range(5, 12)]
        assert all(d > 0 for d in monthly_deltas)


# ---------------------------------------------------------------------------
# Pydantic input validation
# ---------------------------------------------------------------------------

class TestInputValidation:

    def test_velocity_zero_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            ScenarioInput(
                doors=1200, skus=4, unit_price_wholesale=1.00,
                cogs_per_unit=0.45, velocity_units_per_door_per_week=0,
            )
        assert "velocity" in str(exc_info.value).lower()

    def test_cogs_greater_than_price_raises(self):
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=1200, skus=4, unit_price_wholesale=0.40,
                cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
            )

    def test_cogs_equal_to_price_raises(self):
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=1200, skus=4, unit_price_wholesale=0.45,
                cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
            )

    def test_doors_zero_raises(self):
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=0, skus=4, unit_price_wholesale=1.00,
                cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
            )

    def test_skus_zero_raises(self):
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=1200, skus=0, unit_price_wholesale=1.00,
                cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
            )

    def test_invalid_retailer_raises(self):
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=1200, skus=4, unit_price_wholesale=1.00,
                cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
                retailer="target",
            )

    def test_valid_inputs_no_error(self):
        """Control case — valid inputs should not raise."""
        inp = ScenarioInput(
            doors=1200, skus=4, unit_price_wholesale=1.00,
            cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
        )
        assert inp.doors == 1200

    def test_broker_projection_optional(self):
        """broker_projection_year1 is optional — should default to None."""
        inp = ScenarioInput(
            doors=1200, skus=4, unit_price_wholesale=1.00,
            cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
        )
        assert inp.broker_projection_year1 is None
        # effective_broker_projection() should compute a value even when None
        assert inp.effective_broker_projection() > 0

    def test_inf_price_raises(self):
        """float('inf') must be rejected — bypassing this caused the crash path."""
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=1200, skus=4, unit_price_wholesale=float("inf"),
                cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
            )

    def test_nan_price_raises(self):
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=1200, skus=4, unit_price_wholesale=float("nan"),
                cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
            )

    def test_inf_velocity_raises(self):
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=1200, skus=4, unit_price_wholesale=1.00,
                cogs_per_unit=0.45, velocity_units_per_door_per_week=float("inf"),
            )

    def test_doors_upper_bound_raises(self):
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=10_001, skus=4, unit_price_wholesale=1.00,
                cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
            )

    def test_skus_upper_bound_raises(self):
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=1200, skus=101, unit_price_wholesale=1.00,
                cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
            )

    def test_broker_projection_inf_raises(self):
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=1200, skus=4, unit_price_wholesale=1.00,
                cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
                broker_projection_year1=float("inf"),
            )

    def test_broker_projection_negative_raises(self):
        with pytest.raises(ValidationError):
            ScenarioInput(
                doors=1200, skus=4, unit_price_wholesale=1.00,
                cogs_per_unit=0.45, velocity_units_per_door_per_week=2.0,
                broker_projection_year1=-1.0,
            )
