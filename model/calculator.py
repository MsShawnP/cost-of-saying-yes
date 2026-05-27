"""Month-by-month retailer launch cash flow model.

Core insight: cash_received[M] = net_invoiced[M - payment_lag_months].
Invoice date is decoupled from cash receipt date. This creates the cash trough
that makes the "yes to a major retailer" decision dangerous without a working capital plan.
"""

from dataclasses import dataclass
from model.defaults import RETAILER_DEFAULTS, SCENARIO_MULTIPLIERS, WEEKS_PER_MONTH


@dataclass
class ScenarioResult:
    months: list[int]
    gross_revenue: list[float]
    cash_received: list[float]
    deductions: list[float]
    cumulative_cash_position: list[float]
    break_even_month: int | None   # 1-indexed month number, or None
    trough_month: int               # 1-indexed
    trough_value: float
    summary: dict


def calculate_scenario(
    retailer: str,
    doors: int,
    skus: int,
    unit_price_wholesale: float,
    cogs_per_unit: float,
    velocity_units_per_door_per_week: float,
    broker_projection_year1: float,
    scenario: str = "realistic",
) -> ScenarioResult:
    """Run the month-by-month cash flow model for a single scenario."""
    defaults = RETAILER_DEFAULTS[retailer]
    multipliers = SCENARIO_MULTIPLIERS[scenario]

    # Apply scenario multipliers
    velocity = velocity_units_per_door_per_week * multipliers["velocity"]
    chargeback_learning = defaults["chargeback_rate_learning"] * multipliers["chargeback_rate"]
    chargeback_steady = defaults["chargeback_rate_steady"] * multipliers["chargeback_rate"]

    payment_lag = defaults["payment_lag_months"]
    trade_spend_rate = defaults["trade_spend_rate"]
    broker_rate = defaults["broker_commission_rate"]
    ops_overhead = defaults["ops_overhead_monthly"]
    units_per_case = defaults["units_per_case"]

    # Upfront investment (negative cash flow at launch)
    new_store_allowance = (
        defaults["new_store_allowance_per_sku_per_door"] * skus * doors
    )
    slotting = defaults["slotting_per_sku"] * skus
    free_fill_units = skus * doors * units_per_case
    free_fills_cost = free_fill_units * cogs_per_unit
    upfront_investment = -(new_store_allowance + slotting + free_fills_cost)

    # Month-by-month arrays (0-indexed, 12 months)
    months_count = 12
    gross_rev = []
    net_invoiced = []
    deductions_arr = []
    cash_recv = []
    cumulative = []

    units_per_month = doors * skus * velocity * WEEKS_PER_MONTH

    for m in range(months_count):
        gr = units_per_month * unit_price_wholesale
        gross_rev.append(gr)

        cb_rate = chargeback_learning if m < 3 else chargeback_steady
        trade = gr * trade_spend_rate
        chargebacks = gr * cb_rate
        broker = gr * broker_rate
        ded = trade + chargebacks + broker
        deductions_arr.append(ded)

        net_inv = gr - ded
        net_invoiced.append(net_inv)

        # Deduction lag — cash arrives payment_lag months late
        if m >= payment_lag:
            cash_recv.append(net_invoiced[m - payment_lag])
        else:
            cash_recv.append(0.0)

        cogs_month = units_per_month * cogs_per_unit

        if m == 0:
            prev = upfront_investment
        else:
            prev = cumulative[m - 1]

        cumulative.append(prev + cash_recv[m] - cogs_month - ops_overhead)

    # Break-even: first month where cumulative >= 0 (1-indexed)
    break_even_month = None
    for m, val in enumerate(cumulative):
        if val >= 0:
            break_even_month = m + 1
            break

    # Trough: minimum cumulative cash position
    trough_idx = cumulative.index(min(cumulative))
    trough_value = cumulative[trough_idx]
    trough_month = trough_idx + 1

    # Summary
    gross_year1 = sum(gross_rev)
    total_deductions = sum(deductions_arr)
    net_revenue = gross_year1 - total_deductions
    cogs_year1 = units_per_month * cogs_per_unit * months_count
    net_cash_impact = cumulative[-1]  # end-of-year position from zero (pre-launch costs included)

    summary = {
        "gross_revenue_year1": round(gross_year1, 2),
        "total_deductions_year1": round(-total_deductions, 2),   # negative: cost rows render red in Excel
        "net_revenue_year1": round(net_revenue, 2),
        "upfront_investment": round(upfront_investment, 2),       # negative: already negative, abs() removed
        "cogs_year1": round(-cogs_year1, 2),                      # negative: cost rows render red in Excel
        "net_cash_impact_year1": round(net_cash_impact, 2),
        "break_even_month": break_even_month,
        "broker_projection_year1": round(broker_projection_year1, 2),
    }

    return ScenarioResult(
        months=list(range(1, months_count + 1)),
        gross_revenue=[round(v, 2) for v in gross_rev],
        cash_received=[round(v, 2) for v in cash_recv],
        deductions=[round(v, 2) for v in deductions_arr],
        cumulative_cash_position=[round(v, 2) for v in cumulative],
        break_even_month=break_even_month,
        trough_month=trough_month,
        trough_value=round(trough_value, 2),
        summary=summary,
    )


def calculate_all_scenarios(
    retailer: str,
    doors: int,
    skus: int,
    unit_price_wholesale: float,
    cogs_per_unit: float,
    velocity_units_per_door_per_week: float,
    broker_projection_year1: float,
) -> dict[str, ScenarioResult]:
    """Run all three scenarios and return as a dict."""
    return {
        scenario: calculate_scenario(
            retailer=retailer,
            doors=doors,
            skus=skus,
            unit_price_wholesale=unit_price_wholesale,
            cogs_per_unit=cogs_per_unit,
            velocity_units_per_door_per_week=velocity_units_per_door_per_week,
            broker_projection_year1=broker_projection_year1,
            scenario=scenario,
        )
        for scenario in ("optimistic", "realistic", "pessimistic")
    }
