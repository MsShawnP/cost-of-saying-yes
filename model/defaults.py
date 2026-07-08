"""Retailer parameter defaults and the Cinderhaven validated fixture."""

WEEKS_PER_MONTH = 52 / 12  # exact average weeks per calendar month (was 4.33 — rounded, off by $384/yr)

RETAILER_DEFAULTS = {
    "walmart": {
        "payment_lag_months": 1,            # NET-30 — validated by $28M specialty food operator
        "trade_spend_rate": 0.12,
        "chargeback_rate_learning": 0.12,   # months 1-3 — back-solved from Cinderhaven: $14,976 / (3 × $41,600) = 12%
        "chargeback_rate_steady": 0.01,     # months 4-12
        "new_store_allowance_per_sku_per_door": 10.00,
        "slotting_per_sku": 0.00,
        "units_per_case": 40,  # back-solved from Cinderhaven: 4×1200×40×$0.45 = $86,400 free fills
        "broker_commission_rate": 0.05,
        "ops_overhead_monthly": 3232.00,    # validated: $38,784/yr for 1,200-door Walmart account management
    },
    "whole_foods": {
        "payment_lag_months": 1,
        "trade_spend_rate": 0.10,
        "chargeback_rate_learning": 0.03,
        "chargeback_rate_steady": 0.01,
        "new_store_allowance_per_sku_per_door": 0.00,
        "slotting_per_sku": 5000.00,
        "units_per_case": 4,
        "broker_commission_rate": 0.05,
        "ops_overhead_monthly": 1500.00,
    },
    "costco": {
        "payment_lag_months": 1,
        "trade_spend_rate": 0.06,
        "chargeback_rate_learning": 0.04,
        "chargeback_rate_steady": 0.01,
        "new_store_allowance_per_sku_per_door": 0.00,
        "slotting_per_sku": 0.00,
        "units_per_case": 2,
        "broker_commission_rate": 0.05,
        "ops_overhead_monthly": 3500.00,
    },
    "regional_chain": {
        "payment_lag_months": 1,
        "trade_spend_rate": 0.08,
        "chargeback_rate_learning": 0.03,
        "chargeback_rate_steady": 0.005,
        "new_store_allowance_per_sku_per_door": 3.00,
        "slotting_per_sku": 1500.00,
        "units_per_case": 12,
        "broker_commission_rate": 0.05,
        "ops_overhead_monthly": 1000.00,
    },
}

SCENARIO_MULTIPLIERS = {
    "optimistic":  {"velocity": 1.2, "chargeback_rate": 0.7},
    "realistic":   {"velocity": 1.0, "chargeback_rate": 1.0},
    "pessimistic": {"velocity": 0.6, "chargeback_rate": 1.5},
}

# Cinderhaven case-study figures. These ARE the model's own output for the
# Cinderhaven inputs (calculate_scenario on CINDERHAVEN_INPUTS, realistic scenario) —
# not an external target the model is fitted to. Used for all case-study copy and displays.
# The regression test in tests/test_calculator.py pins gross revenue, net cash impact,
# AND the peak trough (value + month) so copy and model cannot drift apart.
#   payment_lag_months=1 (NET-30, Walmart specialty food terms)
#   ops_overhead_monthly=3232 ($38,784/yr for 1,200-door account management)
CINDERHAVEN_VALIDATED = {
    "gross_revenue_year1": 499_200,
    "upfront_allowances": -48_000,
    "free_fills": -86_400,
    "trade_spend": -59_904,
    "learning_curve_chargebacks": -14_976,
    "ongoing_deductions": -3_744,
    "ops_overhead": -38_784,
    "cash_collection_lag": -34_112,
    "broker_commission": -24_960,
    "cogs": -224_640,
    "net_cash_impact_year1": -36_320,
    # Peak trough is structurally Month 1: upfront costs (free fills + allowances)
    # land pre-launch and no cash arrives until Month 2, so the cumulative position
    # is deepest immediately, then climbs back each month.
    "peak_cash_trough": -156_352,
    "peak_cash_trough_month": 1,
}
