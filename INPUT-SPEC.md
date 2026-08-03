# INPUT-SPEC — cost-of-saying-yes (client mode)

This tool is **parameter-driven** — there is no client data file to upload. A client's deal
parameters live in `engagement.yml` under a `deal:` block, and the run produces a branded,
provenance-footed launch-economics report for all three scenarios.

## Required `deal:` parameters

| Parameter | Type | Meaning |
|---|---|---|
| `retailer` | text | One of the known retailer profiles: `walmart`, `whole_foods`, `costco`, `regional_chain` (drives allowances, slotting, trade-spend, terms). |
| `doors` | integer | Number of stores in the launch. |
| `skus` | integer | Number of SKUs. |
| `unit_price_wholesale` | number | Wholesale price per unit ($). |
| `cogs_per_unit` | number | Cost of goods per unit ($). |
| `velocity_units_per_sku_per_door_per_week` | number | Weekly sell-through **per SKU per door**. The model multiplies by doors × SKUs, so this is per-SKU-per-door — not a store total. |
| `broker_projection_year1` | number | The broker's year-1 revenue projection ($), shown alongside the model's own number. |

## Example `engagement.yml`

```yaml
client:
  name: "Meridian Farms"
engagement:
  id: "MER-2026-08"
as_of_date: "2026-07-31"
deal:
  retailer: walmart
  doors: 1200
  skus: 4
  unit_price_wholesale: 1.00
  cogs_per_unit: 0.45
  velocity_units_per_sku_per_door_per_week: 2.0
  broker_projection_year1: 499200
```

## Run

```bash
# with lailara_engagement installed: pip install -e ../engagement-template/lib
python client_mode.py --config engagement.yml --out client-output [--final]
```

Outputs `client-output/launch-economics-report.html` — branded, provenance-footed (parameters
SHA-256, `as_of_date`, config hash), DRAFT-watermarked until `--final`. Every headline number
carries its basis (velocity is per SKU per door; the model multiplies by doors × SKUs).
