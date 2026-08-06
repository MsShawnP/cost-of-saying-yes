"""Client-mode tests for cost-of-saying-yes (parameter-driven, engagement.yml deal block)."""

import pytest

pytest.importorskip("lailara_engagement")

import client_mode  # noqa: E402

_CONFIG = """
client: {name: Meridian Farms}
engagement: {id: MER-2026-08}
as_of_date: 2026-07-31
demo: true
deal:
  retailer: walmart
  doors: 1200
  skus: 4
  unit_price_wholesale: 1.00
  cogs_per_unit: 0.45
  velocity_units_per_sku_per_door_per_week: 2.0
  broker_projection_year1: 499200
"""


@pytest.fixture
def cfg(tmp_path):
    p = tmp_path / "engagement.demo.yml"
    p.write_text(_CONFIG, encoding="utf-8")
    return str(p)


def test_run_matches_engine(cfg, tmp_path):
    result = client_mode.run(cfg, str(tmp_path / "out"))
    # same numbers the engine golden locks
    assert result["net_cash_impact_realistic"] == -36320.0
    assert result["breakeven_velocity"] == 2.54


def test_report_is_branded_and_provenance_footed(cfg, tmp_path):
    result = client_mode.run(cfg, str(tmp_path / "out"))
    html = open(result["report"], encoding="utf-8").read()
    assert "Meridian Farms" in html
    assert "#f5f3ee" in html
    assert "SHA-256" in html
    assert "DRAFT" in html
    assert "per SKU per door" in html  # basis printed with the number


def test_basis_label_pins_the_velocity_unit_basis(cfg, tmp_path):
    """This money tool renders a FIXED basis (velocity per SKU per door per week)
    over its definitional first-12-months horizon — there is no data-dependent
    window to track. The label-text convention here pins the COMPLETE basis
    string; the branding test asserts only 'per SKU per door', which a silent
    edit dropping 'the model multiplies by doors × SKUs' (the clause that makes
    the unit→total scaling explicit) would pass while obscuring what the money
    figure counts."""
    result = client_mode.run(cfg, str(tmp_path / "out"))
    html = open(result["report"], encoding="utf-8").read()
    assert "velocity is per SKU per door per week; the model multiplies by doors × SKUs" in html


def test_missing_deal_param_raises(tmp_path):
    bad = tmp_path / "e.yml"
    bad.write_text(
        "client: {name: X}\nengagement: {id: Y}\nas_of_date: 2026-01-01\n"
        "deal: {retailer: walmart, doors: 100}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing required parameter"):
        client_mode.run(str(bad), str(tmp_path / "out"))


def test_final_drops_watermark(cfg, tmp_path):
    result = client_mode.run(cfg, str(tmp_path / "out"), final=True)
    html = open(result["report"], encoding="utf-8").read()
    assert "ll-draft" not in html
