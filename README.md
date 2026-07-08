# Cost of Saying Yes

An interactive tool that models the actual first-year economics of a major retailer launch — making visible the cash trough that revenue projections hide.

**Live:** https://launch-cost.lailarallc.com

## What it does

Enter your retailer, door count, SKU count, wholesale price, COGS, and velocity. The tool runs a month-by-month cash flow model showing the cumulative cash position across three scenarios (optimistic / realistic / pessimistic), annotates the peak cash trough and break-even month, and downloads a CFO-grade 4-tab Excel model. A Cinderhaven Provisions case study — a brand that saw $499K in projected revenue turn into a −$36K cash year — anchors the numbers to reality.

## Why it matters

Retail launches rarely fail on revenue — they fail on cash. Slotting fees, free-fill product, and chargebacks land before the first payment clears, so a launch that looks profitable on an annual P&L can leave a $3M–$20M brand short of cash in the opening months, when the cash trough is deepest. A founder who can see the depth and timing of the cash trough *before* signing can negotiate terms, stage the door rollout, or line up financing — instead of discovering the gap when payroll is due. The exported Excel model gives the CFO (or the bank) the same numbers in a format they can interrogate.

## Quick start

```bash
pip install -r requirements.txt
ENVIRONMENT=development uvicorn app:app --reload
```

Open http://localhost:8000

`ENVIRONMENT=development` opens CORS to `*` so the frontend can reach the API from any origin during local work.

**Tests:**

```bash
pip install -r requirements-dev.txt
pytest
```

The suite covers the cash flow engine (`tests/test_calculator.py`), the Excel export (`tests/test_excel.py`), and the API (`tests/test_api.py`).

**Deploy** (Fly.io — `fly.toml` and `Dockerfile` included):

```bash
fly deploy
```

## Tech stack

- **Backend:** Python 3.13, FastAPI, Pydantic v2
- **Model:** Custom month-by-month cash flow engine (`model/calculator.py`)
- **Excel:** openpyxl, streamed via BytesIO
- **Frontend:** Vanilla HTML/CSS/JS, Plotly.js
- **Design:** Lailara Design System v2 (Playfair Display + Source Sans 3, Chicago navy)
- **Hosting:** Fly.io (auto-stop/start, shared CPU, 256 MB)

## Project structure

```
app.py            FastAPI app — API endpoints, validation, static file serving
model/
  calculator.py   Month-by-month cash flow engine (three scenarios)
  defaults.py     Retailer defaults and scenario multipliers
  excel.py        4-tab Excel workbook builder
static/           Frontend (index.html, app.js, style.css, Plotly)
tests/            pytest suite: calculator, Excel export, API
```

## Data contract

**Cinderhaven canonical dataset:** 50 SKUs / 5 production lines / 6 retailers.
**Scope:** This is a generic launch economics model. The Cinderhaven case study uses a 4-SKU launch subset, not the full 50-SKU catalog. Audits should not flag the narrower SKU count as data drift.

## License

MIT — see [LICENSE](LICENSE).

---
Built by [Lailara LLC](https://lailarallc.com) — fractional CFO and launch economics advisory for $3M–$20M specialty food brands.
