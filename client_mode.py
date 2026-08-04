"""Client-mode CLI for cost-of-saying-yes.

This tool is parameter-driven (no file intake): a client's deal parameters live
in ``engagement.yml`` under a ``deal:`` block, and the run produces a branded,
provenance-footed, draft-watermarked launch-economics report for all three
scenarios. Uses the shared ``lailara_engagement`` scaffold for config + provenance.

Usage:
    python client_mode.py --config engagement.yml --out client-output [--final]
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from lailara_engagement import build_provenance, load_config
from lailara_engagement import palette as P
from lailara_engagement.provenance import InputRef

from model.calculator import calculate_all_scenarios, calculate_breakeven_velocity
from model.defaults import RETAILER_DEFAULTS

TOOL = "cost-of-saying-yes"
TOOL_VERSION = "1.0"

_REQUIRED = [
    "retailer", "doors", "skus", "unit_price_wholesale",
    "cogs_per_unit", "velocity_units_per_sku_per_door_per_week",
    "broker_projection_year1",
]


def _load_deal(config) -> dict:
    deal = config.raw.get("deal", {}) if isinstance(config.raw, dict) else {}
    missing = [k for k in _REQUIRED if k not in deal]
    if missing:
        raise ValueError(
            "engagement.yml `deal:` block is missing required parameter(s): "
            + ", ".join(missing)
        )
    retailer = str(deal["retailer"]).lower()
    if retailer not in RETAILER_DEFAULTS:
        raise ValueError(
            f"unknown retailer '{retailer}'. Known: {', '.join(RETAILER_DEFAULTS)}"
        )
    return {
        "retailer": retailer,
        "doors": int(deal["doors"]),
        "skus": int(deal["skus"]),
        "unit_price_wholesale": float(deal["unit_price_wholesale"]),
        "cogs_per_unit": float(deal["cogs_per_unit"]),
        # per-SKU-per-door-per-week velocity (the model multiplies by doors AND skus)
        "velocity_units_per_door_per_week": float(deal["velocity_units_per_sku_per_door_per_week"]),
        "broker_projection_year1": float(deal["broker_projection_year1"]),
    }


def _report_html(config, deal, scenarios, breakeven, provenance, *, draft):
    esc = html.escape
    draft_class = " ll-draft" if draft else ""

    def money(v):
        return f"${v:,.0f}"

    rows = ""
    for name in ("optimistic", "realistic", "pessimistic"):
        s = scenarios[name].summary
        rows += (
            f"<tr><td>{esc(name.title())}</td>"
            f"<td class=num>{money(s['gross_revenue_year1'])}</td>"
            f"<td class=num>{money(s['net_revenue_year1'])}</td>"
            f"<td class=num>{money(s['net_cash_impact_year1'])}</td>"
            f"<td class=num>{scenarios[name].trough_month}</td>"
            f"<td class=num>{money(scenarios[name].trough_value)}</td></tr>"
        )
    be_txt = f"{breakeven} units / SKU / door / week" if breakeven else "not reachable at any plausible velocity"
    draft_css = (
        ".ll-draft::before{content:'DRAFT';position:fixed;top:50%;left:50%;"
        "transform:translate(-50%,-50%) rotate(-32deg);font-family:var(--s);"
        "font-size:22vw;font-weight:700;color:rgba(204,16,10,.06);z-index:0;"
        "pointer-events:none;white-space:nowrap}" if draft else ""
    )
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Launch Economics — {esc(config.client_name)}</title><style>
:root{{--s:{P.LL_SERIF};--f:{P.LL_SANS}}}*{{box-sizing:border-box}}
body{{margin:0;background:{P.LL_CANVAS};color:{P.LL_TEXT};font-family:var(--f);line-height:1.6}}
.ll-page{{position:relative;z-index:1;max-width:{P.LL_MAX_WIDTH};margin:0 auto;padding:48px 24px}}
.ll-header{{border-bottom:1px solid {P.LL_GRIDLINE};padding-bottom:24px;margin-bottom:24px}}
.ll-eyebrow{{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:{P.LL_RED};font-weight:600}}
.ll-title{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:34px;margin:8px 0 16px}}
.ll-client{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 24px;font-size:14px}}
.ll-k{{display:block;color:{P.LL_TEXT_SEC};font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
.ll-h2{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:22px;margin:24px 0 12px;padding-bottom:6px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.ll-table{{width:100%;border-collapse:collapse;font-size:14px}}
.ll-table th{{text-align:left;background:{P.LL_CHICAGO};color:#fff;padding:8px 12px}}
.ll-table td{{padding:8px 12px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.ll-note{{background:{P.LL_SURFACE};border-left:3px solid {P.LL_CHICAGO};padding:12px 16px;border-radius:2px;margin-top:16px}}
.ll-provenance{{margin-top:40px;background:{P.LL_CARD_BG};color:{P.LL_CARD_TEXT};padding:20px 24px;border-radius:2px;font-size:13px}}
.ll-prov-title{{font-family:var(--s);font-weight:700;font-size:16px;margin-bottom:8px}}
.ll-provenance div{{margin-bottom:4px;color:{P.LL_CARD_SUBTITLE}}}.ll-provenance strong{{color:{P.LL_CARD_TEXT}}}
.ll-prov-inputs{{width:100%;border-collapse:collapse;margin-top:8px}}
.ll-prov-inputs th{{text-align:left;border-bottom:1px solid rgba(255,255,255,.12);padding:4px 8px;color:{P.LL_CARD_MUTED}}}
.ll-prov-inputs td{{padding:4px 8px;border-bottom:1px solid rgba(255,255,255,.08);color:{P.LL_CARD_SUBTITLE}}}
.ll-prov-brand{{margin-top:12px;font-family:var(--s);color:{P.LL_CARD_MUTED}}}
{draft_css}
@media print{{body{{background:#fff}}}}
</style></head><body class="{draft_class.strip()}"><main class=ll-page>
<header class=ll-header><div class=ll-eyebrow>Lailara LLC · Launch Economics</div>
<h1 class=ll-title>Cost of Saying Yes</h1>
<div class=ll-client>
<div><span class=ll-k>Client</span> {esc(config.client_name)}</div>
<div><span class=ll-k>Engagement</span> {esc(config.engagement_id)}</div>
<div><span class=ll-k>Retailer</span> {esc(deal['retailer'].title())}</div>
<div><span class=ll-k>Doors × SKUs</span> {deal['doors']:,} × {deal['skus']}</div>
<div><span class=ll-k>As of</span> {esc(config.as_of_date.isoformat())}</div>
</div></header>
<h2 class=ll-h2>First-year economics by scenario</h2>
<table class=ll-table><thead><tr><th>Scenario</th><th>Gross rev</th><th>Net rev</th>
<th>Net cash impact</th><th>Trough month</th><th>Trough</th></tr></thead><tbody>{rows}</tbody></table>
<div class=ll-note>Break-even velocity (realistic): <strong>{be_txt}</strong>.
Basis: velocity is per SKU per door per week; the model multiplies by doors × SKUs.</div>
{provenance.to_html()}
</main></body></html>"""


def run(config_path: str, out_dir: str, *, final: bool = False) -> dict:
    config = load_config(config_path)
    deal = _load_deal(config)
    scenarios = calculate_all_scenarios(**deal)
    breakeven = calculate_breakeven_velocity(
        retailer=deal["retailer"], doors=deal["doors"], skus=deal["skus"],
        unit_price_wholesale=deal["unit_price_wholesale"], cogs_per_unit=deal["cogs_per_unit"],
        broker_projection_year1=deal["broker_projection_year1"], scenario="realistic",
    )

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Provenance anchored to the deal parameters (no input file).
    params_blob = json.dumps(deal, sort_keys=True).encode()
    ref = InputRef(filename="engagement.yml (deal parameters)",
                   sha256=hashlib.sha256(params_blob).hexdigest(), n_rows=1, n_cols=len(deal))
    provenance = build_provenance(
        tool=TOOL, tool_version=TOOL_VERSION, inputs=[ref], config=config,
        validation_status="clean",
    )
    report_path = out / "launch-economics-report.html"
    report_path.write_text(
        _report_html(config, deal, scenarios, breakeven, provenance, draft=not final),
        encoding="utf-8",
    )
    return {
        "report": str(report_path),
        "net_cash_impact_realistic": scenarios["realistic"].summary["net_cash_impact_year1"],
        "breakeven_velocity": breakeven,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cost-of-saying-yes client mode")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="client-output")
    ap.add_argument("--final", action="store_true")
    args = ap.parse_args(argv)
    result = run(args.config, args.out, final=args.final)
    print(f"realistic net cash impact Y1: ${result['net_cash_impact_realistic']:,.0f}")
    print(f"break-even velocity: {result['breakeven_velocity']}")
    print(f"report -> {result['report']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
