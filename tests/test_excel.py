"""Tests for the CFO-grade Excel workbook builder.

Covers: sheet structure, byte serialization, cell value mapping, and the
None-break-even fallback string that must not render as Python 'None' in Excel.
"""

import copy
from dataclasses import asdict

import pytest

from model.calculator import calculate_all_scenarios
from model.excel import build_excel_workbook, workbook_to_bytes


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

CINDERHAVEN_INPUTS = dict(
    retailer="walmart",
    doors=1200,
    skus=4,
    unit_price_wholesale=1.00,
    cogs_per_unit=0.45,
    velocity_units_per_door_per_week=2.0,
    broker_projection_year1=499_200,
)


@pytest.fixture(scope="module")
def scenarios():
    """All three scenario results as plain dicts (API response shape)."""
    results = calculate_all_scenarios(**CINDERHAVEN_INPUTS)
    return {k: asdict(v) for k, v in results.items()}


@pytest.fixture(scope="module")
def wb(scenarios):
    """Built workbook (read-only — do not mutate across tests)."""
    return build_excel_workbook(scenarios)


# ---------------------------------------------------------------------------
# Sheet structure
# ---------------------------------------------------------------------------

class TestWorkbookStructure:

    def test_workbook_has_four_sheets(self, wb):
        """Workbook must have exactly Summary + three scenario tabs in order."""
        assert [ws.title for ws in wb.worksheets] == [
            "Summary", "Realistic", "Optimistic", "Pessimistic"
        ]


# ---------------------------------------------------------------------------
# Byte serialization
# ---------------------------------------------------------------------------

class TestWorkbookToBytes:

    def test_returns_nonempty_bytes(self, wb):
        """workbook_to_bytes must return a non-empty bytes object."""
        data = workbook_to_bytes(wb)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_starts_with_xlsx_magic_bytes(self, wb):
        """xlsx is a ZIP file — magic bytes are PK (0x50 0x4B)."""
        data = workbook_to_bytes(wb)
        assert data[:2] == b"PK"


# ---------------------------------------------------------------------------
# Summary sheet cell values
# ---------------------------------------------------------------------------

class TestSummarySheet:

    def test_b2_equals_realistic_gross_revenue(self, wb, scenarios):
        """Summary B2 is Gross Revenue Year 1 for the Realistic scenario."""
        summary_ws = wb["Summary"]
        expected = scenarios["realistic"]["summary"]["gross_revenue_year1"]
        assert summary_ws["B2"].value == expected

    def test_break_even_none_writes_fallback_string(self, scenarios):
        """When break_even_month is None, cell must contain the fallback string,
        not Python None (which would render as an empty cell in Excel).

        Break-Even Month is row 8 in the Summary sheet:
          Row 1 = header, Row 2 = Gross Revenue, ..., Row 8 = Break-Even Month.
        Column B = Realistic scenario.
        """
        # Deep-copy so we don't mutate the module-scoped fixture
        modified = copy.deepcopy(scenarios)
        modified["realistic"]["summary"]["break_even_month"] = None

        test_wb = build_excel_workbook(modified)
        summary_ws = test_wb["Summary"]

        assert summary_ws["B8"].value == "No break-even in 12 months"
