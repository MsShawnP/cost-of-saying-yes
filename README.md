# Cost of Saying Yes

An interactive tool that models the actual first-year economics of a major retailer launch — making visible the cash trough that revenue projections hide.

**Live:** https://launch-cost.lailarallc.com

## What it does

Enter your retailer, door count, SKU count, wholesale price, COGS, and velocity. The tool runs a month-by-month cash flow model showing the cumulative cash position across three scenarios (optimistic / realistic / pessimistic), annotates the peak cash trough and break-even month, and downloads a CFO-grade 4-tab Excel model. A Cinderhaven Provisions case study — a brand that saw $499K in projected revenue turn into a −$36K cash year — anchors the numbers to reality.

## Run locally

```bash
pip install -r requirements.txt
ENVIRONMENT=development uvicorn app:app --reload
```

Open http://localhost:8000

`ENVIRONMENT=development` opens CORS to `*` so the frontend can reach the API from any origin during local work.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

54 tests across `tests/test_calculator.py`, `tests/test_excel.py`, and `tests/test_api.py`.

## Stack

- **Backend:** Python 3.13, FastAPI, Pydantic v2
- **Model:** Custom month-by-month cash flow engine (`model/calculator.py`)
- **Excel:** openpyxl, streamed via BytesIO
- **Frontend:** Vanilla HTML/CSS/JS, Plotly.js
- **Design:** Lailara Design System v2 (Playfair Display + Source Sans 3, Chicago navy)
- **Hosting:** Fly.io (auto-stop/start, shared CPU, 256 MB)

## Data contract

Canonical Cinderhaven conformance — 50 SKUs across 5 product lines and 6 contracted retailers.
## Project

Built by [Lailara LLC](https://lailarallc.com) — fractional CFO and launch economics advisory for $3M–$20M specialty food brands.
