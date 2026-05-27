---
title: "feat: Retailer Launch Cost Model — Interactive Tool + Excel Download"
status: active
created: 2026-05-26
type: feat
---

# feat: Retailer Launch Cost Model — Interactive Tool + Excel Download

**Project:** cost-of-saying-yes  
**Stack:** FastAPI + HTML/JS + Plotly.js + openpyxl → Fly.io  
**Goal:** Ship a CFO-credible interactive tool that makes the invisible cash trough of a major retailer launch visible — month-by-month cumulative cash flow chart, Cinderhaven Walmart case study, downloadable Excel model.

---

## Problem Frame

Specialty food brands ($3M–$20M) evaluate the "yes to a major retailer" decision on revenue projections. Nobody models the cost side — slotting fees, free fills, learning-curve chargebacks, deduction erosion, cash conversion delay. The cumulative cash position in Year 1 is almost always negative before break-even. This tool makes that trough visible.

**Business question:** For a $3M–$20M specialty food brand considering a major retailer, what does saying yes actually cost in the first 12 months, and when does the investment break even?

---

## Scope Boundaries

**In scope (this arc):**
- FastAPI Python backend with `/api/calculate` and `/api/download/excel` endpoints
- HTML/JS single-page frontend with Plotly.js chart and Lailara Design System v2
- Month-by-month cumulative cash flow model with deduction lag (decoupled invoice/cash dates)
- Three scenarios: optimistic / realistic / pessimistic
- Revenue projection vs. net cash reality comparison panel (dark card)
- Cinderhaven Walmart case study (4 SKUs, 1,200 doors, validated numbers)
- openpyxl Excel model: 4 tabs (Summary + 3 scenario tabs), CFO-grade formatting
- Retailer parameter defaults: Walmart and Whole Foods/UNFI
- Fly.io deployment

### Deferred to Follow-Up Work
- Costco-specific mode (roadshow → permanent, pallet/rotation inputs, rotation cliff scenario)
- UNFI/KeHE distributor toggle (double cash conversion hit, distributor margin stacking)
- Board-ready PNG slide export
- Email gating for Excel download
- Additional retailers beyond Walmart and Whole Foods
- Integration with Retail Readiness Scorecard

---

## Key Technical Decisions

1. **FastAPI over Flask.** Automatic Pydantic validation, cleaner JSON, native async. See `DECISIONS.md`.
2. **`plotly-basic.min.js` over D3.** CFO-quality charts, self-hosted, minimal custom JS. See `DECISIONS.md`.
3. **JSON contract defined before frontend work.** Deduction lag is stateful across months; defining the API response shape before writing any JS prevents mid-build data structure reshaping. See `DECISIONS.md`.
4. **Static files served by FastAPI, not a CDN.** Simpler deployment, same-origin in production (no CORS in prod). Self-hosted fonts required by Lailara design system.
5. **`Plotly.react` for scenario toggle.** Handles simultaneous data + layout updates in one call — the annotation positions (trough, break-even) change across scenarios, requiring a layout update alongside data. `restyle` handles data only; `relayout` handles layout only; `Plotly.react` handles both.
6. **Comparison panel as plain HTML/CSS dark card.** Two headline numbers don't need a chart engine. Using Lailara's `#1a1a1a` dark card pattern directly is faster and gives more design control.
7. **Excel streamed via `BytesIO`.** No disk writes. `openpyxl` saves to a `BytesIO` buffer; FastAPI's `StreamingResponse` serves it.
8. **Fly.io port 8080.** Fly.io's default `internal_port`. Must match the `CMD` in the Dockerfile and `internal_port` in `fly.toml`. (Using 8000 requires changing both — 8080 is the path of least resistance.)

---

## JSON API Contract

Both U2 (Python model) and U5 (frontend JS) must conform to this shape exactly. Define it as a Pydantic response model in `app.py`.

**`POST /api/calculate` — Request:**
```json
{
  "retailer": "walmart",
  "doors": 1200,
  "skus": 4,
  "unit_price_wholesale": 1.00,
  "cogs_per_unit": 0.45,
  "velocity_units_per_door_per_week": 2.0,
  "broker_projection_year1": 499200
}
```

**`POST /api/calculate` — Response** (all three scenarios in one call — avoids three round trips for the scenario toggle):
```json
{
  "optimistic": { ... scenario shape ... },
  "realistic":  { ... scenario shape ... },
  "pessimistic": { ... scenario shape ... }
}
```

**Per-scenario shape:**
```json
{
  "months": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
  "gross_revenue": [41600, ...],
  "cash_received":  [0, 0, 35000, ...],
  "deductions":     [4992, ...],
  "cumulative_cash_position": [-48000, -96000, -106000, ...],
  "break_even_month": 9,
  "trough_month": 4,
  "trough_value": -165000,
  "summary": {
    "gross_revenue_year1": 499200,
    "total_deductions_year1": 83904,
    "net_revenue_year1": 415296,
    "upfront_investment": 134400,
    "cogs_year1": 224640,
    "net_cash_impact_year1": -36320,
    "break_even_month": 9
  }
}
```

`break_even_month` is `null` if cumulative cash never crosses zero within 12 months.

---

## Output Structure

```
cost-of-saying-yes/
├── app.py                     # FastAPI app: middleware, routes, StaticFiles mount
├── model/
│   ├── __init__.py
│   ├── calculator.py          # core financial model engine
│   └── defaults.py            # retailer parameter defaults (Walmart, Whole Foods)
├── static/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   ├── plotly-basic.min.js    # self-hosted Plotly.js basic bundle
│   └── fonts/
│       ├── playfair-display-700.woff2
│       ├── playfair-display-400.woff2
│       ├── source-sans-3-400.woff2
│       └── source-sans-3-600.woff2
├── tests/
│   ├── __init__.py
│   └── test_calculator.py
├── requirements.txt
├── Dockerfile
└── fly.toml
```

---

## Implementation Units

### U1. Project scaffold and configuration

**Goal:** Create the full directory structure, dependency file, and a working FastAPI skeleton that serves `index.html` from `/`. No model logic yet.

**Files:**
- `requirements.txt` (create)
- `app.py` (create — skeleton only)
- `model/__init__.py` (create — empty)
- `static/index.html` (create — minimal placeholder)
- `Dockerfile` (create)
- `fly.toml` (create)

**Approach:**

`requirements.txt`: Two lines — `fastapi[standard]` and `openpyxl`. `fastapi[standard]` includes uvicorn, python-multipart, and pydantic.

`app.py` ordering is critical — StaticFiles acts as a catch-all; if mounted before API routes, it intercepts everything:
1. `mimetypes.add_type("application/javascript", ".js")` and `mimetypes.add_type("text/css", ".css")` — Windows MIME bug fix (Starlette reads MIME types from the Windows registry; `.js` may resolve to `text/plain` without this)
2. `CORSMiddleware` — allow all origins when `ENVIRONMENT=development`, restrict to Fly.io domain when `ENVIRONMENT=production`. Read from env var.
3. API route registrations (`@app.post("/api/calculate")`, etc.)
4. `app.mount("/", StaticFiles(directory="static", html=True), name="static")` — **last**. The `html=True` flag serves `index.html` for any path not matched above (correct SPA behavior).

`Dockerfile`: `python:3.12-slim`, copy `requirements.txt` first for layer cache, `pip install --no-cache-dir -r requirements.txt`, copy app code, `EXPOSE 8080`, CMD `uvicorn app:app --host 0.0.0.0 --port 8080`.

`fly.toml`: `internal_port = 8080` (matches Dockerfile CMD), `auto_stop_machines = "stop"` (scale to zero when idle — cost saving), `ENVIRONMENT = "production"` in `[env]`, `force_https = true`.

**Test scenarios:**
- `uvicorn app:app --reload` starts without import errors
- `GET /` returns 200 with `Content-Type: text/html`
- `GET /nonexistent` returns `index.html` (not 404) — SPA routing
- On Windows dev: `GET /app.js` returns `Content-Type: application/javascript` (MIME fix confirmed)

**Verification:** Start with `uvicorn app:app --reload`; open `http://localhost:8000/`; see placeholder HTML; confirm no console errors.

---

### U2. Financial model engine

**Goal:** Implement `model/calculator.py` with the month-by-month cash flow model, Pydantic input/output models, and retailer defaults. The deduction lag — decoupling invoice date from cash receipt date — is the core architectural challenge.

**Dependencies:** U1

**Files:**
- `model/calculator.py` (create)
- `model/defaults.py` (create)
- `app.py` (modify — add Pydantic `ScenarioInput` and `ScenarioResult` models)

**Approach:**

**The deduction lag (this is the key):**

Cash flows are stateful across months. `cash_received[M]` equals `net_invoiced[M - payment_lag_months]`, zero-padded for months before the first payment clears. This is not the same as subtracting deductions from the same month's revenue:

```
Pre-launch (month 0):
  cumulative_cash[0] = -(slotting + free_fills + edi_setup)

For each month M in 1..12:
  units_sold     = doors × skus × velocity × 4.33
  gross_rev[M]   = units_sold × unit_price_wholesale
  
  trade_spend[M] = gross_rev[M] × trade_spend_rate
  chargebacks[M] = gross_rev[M] × chargeback_rate(M)  # 3% months 1-3, 1% months 4-12
  broker[M]      = gross_rev[M] × broker_commission_rate
  deductions[M]  = trade_spend[M] + chargebacks[M] + broker[M]
  
  net_invoiced[M] = gross_rev[M] - deductions[M]
  
  # Cash arrives late — decoupled from invoice
  cash_received[M] = net_invoiced[M - payment_lag] if M > payment_lag else 0
  
  cogs[M]        = units_sold × cogs_per_unit
  
  cumulative_cash[M] = cumulative_cash[M-1] + cash_received[M] - cogs[M] - ops_overhead_monthly
```

**Break-even detection:** First month M where `cumulative_cash[M] >= 0`. Returns `None` if never positive within 12 months.

**Scenario multipliers** applied to velocity and chargeback rates before running the model:
- Optimistic: velocity × 1.2, chargeback_rate × 0.7
- Realistic: base parameters
- Pessimistic: velocity × 0.6, chargeback_rate × 1.5

**Retailer defaults (`model/defaults.py`):**
Dict keyed by `"walmart"` and `"whole_foods"`. Each entry:
- `payment_lag_months` (2 for Walmart, 1 for Whole Foods via UNFI)
- `trade_spend_rate` (0.12 Walmart, 0.10 Whole Foods)
- `chargeback_rate_learning` (months 1-3: 0.03)
- `chargeback_rate_steady` (months 4-12: 0.01)
- `new_store_allowance_per_sku_per_door` (Walmart: $10, Whole Foods: $0 — uses slotting instead)
- `slotting_per_sku` (Walmart: $0, Whole Foods: $5,000)
- `free_fill_case_cogs_per_sku_per_door` (derived from COGS × units_per_case)
- `units_per_case` (4 — drives free fill calculation; user can override)
- `broker_commission_rate` (0.05)
- `ops_overhead_monthly` (derived from tier or user input)

**Cinderhaven hardcoded fixture** in `defaults.py` as a separate dict constant (not computed from the model) — the validated numbers from the brief used in the case study section. Separating validated case study numbers from computed model outputs avoids any rounding discrepancy.

**Pydantic `ScenarioInput`** (in `app.py`):
- Validators: `velocity > 0`, `cogs_per_unit < unit_price_wholesale`, `doors > 0`, `skus > 0`, all numeric fields positive. FastAPI returns 422 with field-level error detail automatically.

**Patterns to follow:** Pydantic v2 `field_validator` with `info.data` for cross-field validation (COGS < price check).

**Test scenarios:** Covered in U3.

**Verification:** Import `calculator.py` in a Python REPL; run Cinderhaven inputs; confirm `summary.net_cash_impact_year1 ≈ -$36,320` and `break_even_month` in expected range (8–12).

---

### U3. Unit tests for the financial model

**Goal:** Verify the core calculation logic in isolation — deduction lag, break-even detection, scenario multipliers, edge cases, and the Cinderhaven reference scenario.

**Dependencies:** U2

**Files:**
- `tests/__init__.py` (create — empty)
- `tests/test_calculator.py` (create)

**Approach:** pytest. Import calculator functions directly, not via the API layer.

**Test scenarios:**

*Happy path:*
- Cinderhaven realistic: gross revenue ≈ $499,200, net cash impact ≈ -$36,320, break-even month between 8 and 12
- `cumulative_cash_position` array has at least one negative value followed by positive values at `break_even_month`
- `cash_received[M]` for M ≤ `payment_lag_months` equals 0
- `cash_received[M]` for M > `payment_lag_months` equals `net_invoiced[M - payment_lag_months]`

*Deduction lag (the critical invariant):*
- Month 1 deductions appear in `net_invoiced[0]` but `cash_received[0] = 0`
- With 2-month lag: `cash_received[2] == net_invoiced[0]` (0-indexed arrays)

*Scenarios:*
- Optimistic `net_cash_impact_year1` > realistic `net_cash_impact_year1`
- Pessimistic `net_cash_impact_year1` < realistic `net_cash_impact_year1`
- Pessimistic `break_even_month` >= realistic `break_even_month` (or None)

*Break-even edge cases:*
- Pessimistic with very low velocity: `break_even_month` is `None`
- Very high velocity: `break_even_month` is month 1 or 2

*Input validation (via Pydantic model):*
- `velocity_units_per_door_per_week = 0` raises `ValidationError`
- `cogs_per_unit >= unit_price_wholesale` raises `ValidationError`
- `doors = 0` raises `ValidationError`

**Verification:** `pytest tests/ -v` passes with zero failures.

---

### U4. FastAPI API layer

**Goal:** Implement the two API endpoints — `POST /api/calculate` (returns all three scenarios) and `GET /api/download/excel` (streams the Excel workbook).

**Dependencies:** U2, U3

**Files:**
- `app.py` (modify — add full endpoint implementations)

**Approach:**

`POST /api/calculate`: Accepts `ScenarioInput`, runs the model three times (optimistic, realistic, pessimistic), returns `ScenarioResult` with all three scenarios. Computing all three in one call avoids three round trips for the scenario toggle.

`GET /api/download/excel`: Query params `retailer` (default `"walmart"`) and `scenario` (default `"realistic"`). Calls `build_excel_workbook()` (implemented in U7), saves to `BytesIO`, returns:
```python
StreamingResponse(
    buffer,
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    headers={"Content-Disposition": "attachment; filename=retailer-launch-model.xlsx"}
)
```

**Error handling:** Pydantic validation failures return 422 automatically. No custom error middleware needed for MVP — FastAPI's default 500 handler is sufficient.

**Test scenarios:**
- `POST /api/calculate` with valid Cinderhaven inputs returns 200 with `optimistic`, `realistic`, `pessimistic` keys
- All three scenario objects contain `months` (length 12), `cumulative_cash_position` (length 12), `summary`, `break_even_month`
- `POST /api/calculate` with `velocity=0` returns 422 with a `detail` array mentioning the `velocity` field
- `POST /api/calculate` with `cogs_per_unit > unit_price_wholesale` returns 422
- `GET /api/download/excel` returns 200 with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `GET /api/download/excel` response has `Content-Disposition: attachment; filename=retailer-launch-model.xlsx`

**Verification:** Use FastAPI's auto-generated `/docs` UI to call both endpoints manually; confirm responses match the contract.

---

### U5. Frontend shell — HTML, CSS, Lailara tokens, fonts, input form

**Goal:** Build the complete frontend shell: self-hosted fonts, Lailara CSS custom properties, input form that collects user parameters, and wired fetch call to `POST /api/calculate`.

**Dependencies:** U1, U4

**Files:**
- `static/index.html` (replace placeholder with full structure)
- `static/style.css` (create)
- `static/app.js` (create — form wiring and fetch)
- `static/fonts/` (populate with woff2 files)

**Approach:**

**Fonts:** Download woff2 files for Playfair Display 400/700 and Source Sans 3 400/600. Define `@font-face` rules in `style.css` pointing to `/fonts/...`. Do NOT use the Google Fonts CDN — Lailara design system requires self-hosting.

**CSS custom properties** (define on `:root`):
```css
--color-canvas:      #f5f3ee;
--color-text:        #333333;
--color-text-muted:  #595959;
--color-gridline:    #d9d9d9;
--color-reference:   #666666;
--color-navy:        #1f2e7a;
--color-navy-hover:  #141e52;
--color-red:         #cc100a;
--color-dark-card:   #1a1a1a;
--color-teal:        #158f75;
--font-serif: 'Playfair Display', Georgia, 'Times New Roman', serif;
--font-sans:  'Source Sans 3', 'Source Sans Pro', 'Helvetica Neue', Arial, sans-serif;
```

**Page layout:**
- `max-width: 900px`, centered, `padding: 48px 24px` desktop / `32px 16px` mobile
- `background-color: var(--color-canvas)` on `body`
- `border-radius: 2px` on all card/panel elements (minimal, not rounded)

**Input form fields:**
- Retailer selector: `<select>` with Walmart / Whole Foods options — changing retailer pre-fills velocity and payment term hints
- Doors, SKUs: integer inputs
- Wholesale price per unit ($), COGS per unit ($), velocity (units/door/week): numeric inputs
- Broker's Year 1 revenue projection ($): numeric input (for comparison panel)
- "Calculate" button: Navy background `#1f2e7a`, white text, 600 weight, hover darkens to `#141e52`, `border-radius: 2px`

**Fetch call in `app.js`:**
1. On "Calculate" click: disable button, set text to "Calculating…"
2. `fetch('/api/calculate', { method: 'POST', body: JSON.stringify(formValues), headers: {'Content-Type': 'application/json'} })`
3. On response: store all three scenario objects in a module-level `currentData` variable
4. Call `renderScenario('realistic')` to render the default scenario
5. Enable scenario toggle buttons; re-enable Calculate button

**Scenario toggle buttons:** Three buttons — Optimistic / Realistic / Pessimistic. Active button: navy background. Inactive: transparent with navy border. Clicking calls `renderScenario(key)` which reads from `currentData[key]`.

**Excel download button:** `<a href="/api/download/excel">Download Excel Model</a>` — rendered as a styled button. No JS needed; browser handles the file download.

**Test scenarios:**
- Form renders with Walmart defaults visible in input placeholders/hints
- Switching retailer selector to Whole Foods updates default hints
- Clicking Calculate with empty required fields triggers browser native validation (use `required` attributes)
- Calculate button shows "Calculating…" text during fetch and restores after
- After successful fetch, scenario toggle buttons become active (not disabled)
- Keyboard navigation: tab order flows logically through inputs

**Verification:** Open `http://localhost:8000/`, tab through all inputs, fill in Cinderhaven values, click Calculate. No console errors. Scenario toggle buttons are enabled after response.

---

### U6. Plotly.js cash flow chart, comparison panel, and scenario toggle

**Goal:** Implement the centerpiece cumulative cash flow chart with break-even annotation and trough callout, the revenue-vs-reality dark card comparison panel, and the three-scenario toggle — all using Lailara design system tokens.

**Dependencies:** U5

**Files:**
- `static/plotly-basic.min.js` (add — download from Plotly.js dist)
- `static/index.html` (modify — add `<script src="/plotly-basic.min.js">` and container elements)
- `static/app.js` (modify — add chart and panel rendering)

**Approach:**

**Load Plotly.js:** Plain `<script src="/plotly-basic.min.js">` tag, not an ES module. Attaches `Plotly` to `window`. Download the `plotly-basic.min.js` dist file (~365 kB gzipped) and place in `static/`. Do not use CDN.

**Chart container:** `<div id="cashflow-chart" style="width:100%; height:420px;"></div>`

**Initial render:** `Plotly.newPlot('cashflow-chart', [trace], layout, config)` when API response arrives.

**Scenario switch:** `Plotly.react('cashflow-chart', [newTrace], newLayout, config)` — one call handles both data and layout. Always pass a **new array reference** for `y` data: `y: [...scenarioData.cumulative_cash_position]`. Never mutate the existing array — `Plotly.react` uses `===` identity to detect changes; mutation causes no redraw.

**Chart Lailara tokens:**
- `paper_bgcolor` AND `plot_bgcolor`: `#f5f3ee` (both must be set — `paper_bgcolor` is the margin area, `plot_bgcolor` is inside the axes)
- Line: color `#1f2e7a`, width 2.5
- Area fill: `tozeroy`, `fillcolor: 'rgba(31, 46, 122, 0.08)'`
- Gridlines: `gridcolor: '#d9d9d9'`, horizontal only (`xaxis.showgrid: false`)
- Zero line: `zerolinecolor: '#666666'`, width 2 (a reference line, not data)
- Break-even line: `layout.shapes` entry, `type: 'line'`, `xref: 'x'`, `yref: 'paper'` (full height), color `#cc100a`, `dash: 'dash'`
- Break-even label: annotation at top of chart, `#cc100a` text
- Cash trough callout: annotation with arrow, `bgcolor: '#1a1a1a'`, white text (Lailara dark card)
- Font family: Source Sans 3 throughout axis labels and tick text

**`buildLayout(breakEvenMonth, troughMonth, troughValue)` function:** Extract the full layout object into a function so `switchScenario` can rebuild it without duplicating the config. Called once on initial render, again on each scenario switch.

**Config:** `{ responsive: true, displaylogo: false, displayModeBar: false }` — hides Plotly toolbar for clean CFO presentation.

**Resize handler:** `window.addEventListener('resize', () => Plotly.Plots.resize('cashflow-chart'))`.

**Comparison panel (plain HTML/CSS):**
Structure:
```
┌──────────────────────────────────────────┐  background #1a1a1a
│  BROKER PROJECTION   │  NET CASH IMPACT  │  label: Source Sans 3 14px #9a9a9a uppercase
│  $499,200            │  -$36,320         │  value: Playfair Display 64px (44px mobile) 700
│  Year 1 gross        │  After all costs  │  sub: Source Sans 3 14px #9a9a9a
└──────────────────────────────────────────┘  divider: rgba(255,255,255,0.12) 1px
```
- Negative `net_cash_impact_year1` value displays in brand red `#cc100a`
- Update via `element.textContent = formatCurrency(value)` after each `renderScenario()` call

**`formatCurrency(n)` helper:** Compact format — `$1.2M`, `$300K`, `$42K`, `$-637K`. Apply sign separately from magnitude.

**Test scenarios:**
- Chart renders after Calculate (realistic scenario by default)
- Break-even vertical dashed line appears at the month indicated by `break_even_month`
- Cash trough annotation shows the correct dollar value from `trough_value`
- Switching to pessimistic: chart updates, trough goes deeper, break-even moves later (or disappears)
- Switching to optimistic: chart updates, trough is shallower, break-even is earlier
- Comparison panel: negative `net_cash_impact_year1` renders in red
- Resizing browser window: chart reflows within container, does not overflow
- `break_even_month: null` (pessimistic worst case): chart renders without error, break-even line absent

**Verification:** Visual inspection at desktop (1200px) and mobile (375px) widths. Cross-check trough value and break-even month against expected Cinderhaven realistic figures.

---

### U7. openpyxl Excel workbook

**Goal:** Build a CFO-grade Excel model with 4 tabs (Summary + 3 scenario tabs), formatted for board presentation, streamed via the download endpoint.

**Dependencies:** U2, U4

**Files:**
- `model/excel.py` (create — `build_excel_workbook(scenarios: dict) -> Workbook`)
- `app.py` (modify — import `build_excel_workbook` in the download endpoint)

**Approach:**

**Tab structure:**
1. `Summary` (index 0): Key metrics side-by-side across all three scenarios — gross revenue, total deductions, net revenue, upfront investment, COGS, net cash impact, break-even month. Assumption inputs listed below.
2. `Realistic`, `Optimistic`, `Pessimistic`: Full 12-month detail — month, gross revenue, deductions, net invoiced, cash received, cumulative cash, deduction rate.

**NamedStyles — register on workbook BEFORE writing any cells** (openpyxl raises `KeyError` if you reference a style before registering it):
- `header`: Chicago navy fill (`#1F2E7A`), white bold font, centered alignment
- `currency`: `"$"#,##0` format, right-aligned
- `neg_currency`: `"$"#,##0;[Red]("$"#,##0)` — red parentheses for negative values
- `pct`: `0.0%` format

**On every sheet:**
- `ws.freeze_panes = "A2"` (freeze header row — `"A2"` freezes only row 1, `"B2"` would freeze row 1 AND column A)
- Print area set to data range
- `ws.print_title_rows = "1:1"` (repeat header on every printed page)
- Landscape orientation, fit to 1 page wide, letter size
- Footer: left = `"Confidential — Lailara LLC"`, right = `"Page &P of &N"`

**Column widths:** Hardcode for fixed schema (month=12, currency columns=16, percentage columns=14). Content-driven auto-width is unreliable in openpyxl; fixed widths produce tighter results.

**Remove default sheet:** `wb.remove(wb.active)` immediately after `wb = Workbook()`.

**`BytesIO` pattern:**
```python
buffer = BytesIO()
wb.save(buffer)
buffer.seek(0)
return StreamingResponse(buffer, media_type="...", headers={...})
```

**Test scenarios:**
- Downloaded file opens in Excel/LibreOffice without errors
- 4 tabs present, named correctly (no default "Sheet1")
- Row 1 frozen: scrolling rows does not lose headers
- Currency cells show `$` and comma separators
- Negative values display in red with parentheses
- Print preview shows only the data range (print area is set)
- Footer appears in print preview: "Confidential — Lailara LLC" / "Page 1 of N"

**Verification:** Download via `GET /api/download/excel`, open in Excel, visually inspect all 4 tabs. Verify freeze and print settings in Excel's Page Layout view.

---

### U8. Cinderhaven Walmart case study section

**Goal:** Add a static case study section below the interactive tool — validated numbers table, before/after framing, Economist-voice narrative.

**Dependencies:** U5 (HTML shell)

**Files:**
- `static/index.html` (modify — add case study section)
- `static/style.css` (modify — case study section styles)

**Approach:**

The case study is pure static HTML. No JavaScript, no dynamic rendering. Validated numbers are hardcoded in the markup.

**Section structure:**
1. **Eyebrow:** `"CASE STUDY"` — Source Sans 3 12px uppercase, brand red `#cc100a`, letter-spacing 0.04em
2. **Headline:** `"Cinderhaven Provisions: The $499K Question"` — Playfair Display 22px 700
3. **Setup:** 1-2 sentence framing paragraph. Economist voice. 50 words max.
4. **The gap callout:** Dark card (`#1a1a1a`) with two columns — broker's projection vs. net cash impact. Same pattern as the interactive comparison panel. Static values.
5. **Numbers table:** Economist-style breakdown table — clean horizontal rules, no decorative vertical borders. Source footnote below.
6. **Insight paragraph:** 2-3 sentences. The cash trough, the working capital requirement, what the model reveals that the revenue projection hides.

**Validated Cinderhaven numbers (confirmed by $28M specialty food operator):**
| Line item | Amount |
|---|---|
| Gross Year 1 Revenue | $499,200 |
| Upfront Allowances (New Store) | -$48,000 |
| Free Fills (1 case/SKU/door) | -$86,400 |
| Trade Spend (12% of net) | -$59,904 |
| Learning-Curve Chargebacks (months 1–3) | -$14,976 |
| Ongoing Deductions (1% steady-state) | -$4,992 |
| Broker Commission (5%) | -$24,960 |
| COGS | -$224,640 |
| **Net Year 1 Cash Impact** | **-$36,320** |
| **Peak Cash Trough (Month 4)** | **-$165,000** |

**Voice:** Sober, declarative, data-forward. "The brand requires $165,000 in working capital to fund the Walmart launch through Month 4. Revenue recognition and cash collection are not the same thing." No marketing language.

**Test scenarios:**
- Case study section renders below the interactive tool
- Table values match the validated Cinderhaven figures exactly
- Dark card callout: white text readable on `#1a1a1a` background
- Source footnote is present below the table
- Section readable at mobile width (375px) without horizontal scroll

**Verification:** Visual inspection at desktop and mobile widths. Confirm table values against brief line-by-line.

---

### U9. Deployment

**Goal:** Deploy to Fly.io; publicly accessible at a stable HTTPS URL.

**Dependencies:** All prior units

**Files:**
- `Dockerfile` (finalize from U1 skeleton)
- `fly.toml` (finalize from U1 skeleton)
- `.gitignore` (verify covers `__pycache__/`, `.venv/`, `.env`)

**Approach:**

**Pre-deploy checklist:**
- `pytest tests/` passes
- `uvicorn app:app` starts; `http://localhost:8000/` renders the tool end-to-end
- No hardcoded secrets in any file
- `.gitignore` covers `__pycache__/`, `*.pyc`, `.venv/`, `.env`

**Dockerfile (final):**
- `python:3.12-slim` base
- Copy `requirements.txt` first → `pip install` → copy app code (Docker layer cache order)
- `EXPOSE 8080`
- `CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]`

**fly.toml (final):**
- `internal_port = 8080` — must match Dockerfile CMD exactly
- `auto_stop_machines = "stop"` — scale to zero when idle
- `ENVIRONMENT = "production"` in `[env]`
- `force_https = true`
- Health check: `GET /` every 30s, 5s timeout

**Deploy sequence:**
1. `fly launch` (first time — creates app; decline Postgres when asked)
2. Answer "no" to "overwrite existing fly.toml?" if prompted
3. `fly deploy`
4. `fly open` — opens live URL in browser

**Test scenarios:**
- `fly status` shows machine running and healthy
- Live URL returns the tool (not a Fly.io error page)
- `POST /api/calculate` works from the live frontend
- Excel download triggers a file download (not rendered inline)
- HTTPS enforced — HTTP redirects to HTTPS

**Verification:** Open the live URL on a different device (phone or different browser). Fill in Cinderhaven values, click Calculate, confirm chart renders and Excel downloads.

---

## Risks

**Cinderhaven number precision:** The hardcoded case study numbers and the calculator's computed output may diverge slightly due to rounding (e.g., `4.33` weeks/month approximation). Resolution: treat the hardcoded case study numbers as authoritative for the case study narrative; the interactive tool produces its own computed output. Document any discrepancy > 5% in a FAILURES.md entry.

**`units_per_case` ambiguity:** The free fill calculation requires knowing how many units are in a case. Back-solve from the Cinderhaven validated numbers (4 SKUs × 1,200 doors × X units × $0.45 COGS = $86,400 → X = 40 units/case) or make it an explicit retailer default. Resolve in U2.

**Fly.io cold start:** With `auto_stop_machines = "stop"`, the first request after idle may take 2–4 seconds. Acceptable for this use case. If it becomes noticeable, add a "loading" state to the Calculate button.

**Plotly.js CSP:** The `plotly-basic.min.js` bundle uses `new Function()` internally, which requires `unsafe-eval` under a strict Content-Security-Policy. Skip CSP headers for MVP — this tool handles no private data.

---

## Deferred Implementation Questions

- Whether `broker_projection_year1` should be optional (with a computed default = `gross_revenue_year1`) or required — decide in U2/U5
- Mobile breakpoint exact pixel values for the comparison panel — follow design system `640px` breakpoint
- Exact woff2 file naming convention for the fonts directory — follow Google Fonts download naming

---

## Definition of Done

- [ ] Core model calculates month-by-month cash flow correctly — deduction lag decoupled from invoice date
- [ ] Cinderhaven Walmart scenario matches the validated numbers from brief
- [ ] Chart renders cleanly and shows the cash trough and break-even month
- [ ] Three scenarios work and produce meaningfully different outputs
- [ ] Excel downloads and is formatted well enough to hand to a CFO
- [ ] `pytest tests/` passes with zero failures
- [ ] Deployed and accessible at a public URL
- [ ] Someone other than you can use it without explanation
