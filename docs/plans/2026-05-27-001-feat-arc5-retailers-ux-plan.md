---
id: 2026-05-27-001
title: "Arc 5: New retailers (Costco + Regional chain) + UX polish"
status: active
created: 2026-05-27
feature: arc5-retailers-ux
---

# Arc 5: New retailers + UX polish

## Problem frame

The tool currently models Walmart and Whole Foods. Two high-value retailer types
are missing: Costco (warehouse/club — fundamentally different economics, no broker,
no chargebacks, small case pack) and Regional Chain (mid-tier, common first launch
target for $3M–$20M brands). The comparison view is also absent — a CFO evaluating
multiple retailer options has to run the tool multiple times and hold numbers in
their head. Three UX gaps degrade the experience: validation errors are page-level
blobs rather than inline, chart hovers show no monthly breakdown, and there is no
side-by-side retailer comparison.

This arc fixes all of the above.

## Scope

### In scope

- Add Costco + Regional chain retailer defaults to `model/defaults.py`
- Add Costco + Regional chain to the retailer dropdown in `static/index.html`
- New `POST /api/compare` endpoint: accepts brand inputs (no retailer field), runs
  the realistic scenario for all four retailers, returns a summary table
- Retailer comparison metrics table in the results panel (trough, break-even, net
  cash Y1 per retailer)
- Inline per-field validation error spans beneath each input (replaces single
  page-level `#form-error`)
- Chart hover tooltip with monthly breakdown (Gross Revenue, Deductions, Cash
  Received, Cumulative) via Plotly customdata

### Out of scope

- Retailer overlay chart (two or more retailers on the same axis) — complexity not
  justified at this stage; the metrics table is enough
- User-editable retailer defaults
- Additional scenario types beyond optimistic/realistic/pessimistic
- Email capture or lead gen gating

## Retailer defaults (confirmed)

### Costco

| Key | Value |
|-----|-------|
| payment_lag_months | 1 |
| trade_spend_rate | 0.06 |
| chargeback_rate_learning | 0.04 |
| chargeback_rate_steady | 0.01 |
| new_store_allowance_per_sku_per_door | 0.00 |
| slotting_per_sku | 0.00 |
| units_per_case | 2 |
| broker_commission_rate | 0.05 |
| ops_overhead_monthly | 3500.00 |

### Regional chain

| Key | Value |
|-----|-------|
| payment_lag_months | 1 |
| trade_spend_rate | 0.08 |
| chargeback_rate_learning | 0.03 |
| chargeback_rate_steady | 0.005 |
| new_store_allowance_per_sku_per_door | 3.00 |
| slotting_per_sku | 1500.00 |
| units_per_case | 12 |
| broker_commission_rate | 0.05 |
| ops_overhead_monthly | 1000.00 |

## Existing patterns to follow

- **Retailer defaults:** `model/defaults.py` — `RETAILER_DEFAULTS` dict; the
  `retailer_valid` Pydantic validator in `ScenarioInput` auto-accepts new keys
  from this dict, so adding defaults is all that's needed for the backend
- **Dropdown options:** `static/index.html` — follow the `<option value="walmart">`,
  `<option value="whole_foods">` pattern; key must match the `RETAILER_DEFAULTS` key
- **Form field validation:** `ScenarioInput` validators in `app.py` use
  `@field_validator` with `mode='before'`; `@model_validator` for cross-field
  (cogs < price). Frontend mirrors server validation for instant feedback.
- **API endpoint pattern:** `/api/calculate` — `POST` accepting `ScenarioInput`,
  returning JSON. The compare endpoint follows the same shape but uses a different
  input model (no `retailer` field) and a different response shape.
- **Plotly customdata:** set `customdata` as a list-of-lists parallel to `x`; use
  `%{customdata[0]}` etc. in `hovertemplate`. Currently no customdata on the trace.
- **Test patterns:** `tests/test_api.py` uses `TestClient(app)`, groups tests by
  concern in classes, shares `VALID_PAYLOAD` from `from conftest import CINDERHAVEN_INPUTS`.
  New endpoint tests follow this pattern.

## API design

### New endpoint: `POST /api/compare`

**Input model** (separate Pydantic model `CompareInput`):
- Same fields as `ScenarioInput` minus `retailer`
- Same validators (doors, skus, price, cogs, velocity, broker)
- Pydantic root validator for `cogs < price`

**Response shape:**
```json
{
  "retailers": [
    {
      "key": "walmart",
      "label": "Walmart",
      "trough_value": -36000,
      "trough_month": 4,
      "break_even_month": 9,
      "net_cash_impact_year1": -36000
    },
    ...
  ]
}
```

**Implementation:** call `calculate_scenario(retailer=key, ...)` for each key in
`RETAILER_DEFAULTS`, scenario fixed to `"realistic"`. Return a sorted list
(by `net_cash_impact_year1` descending — best to worst).

**Retailer labels** (display names mapped from keys):
- `walmart` → "Walmart"
- `whole_foods` → "Whole Foods / UNFI"
- `costco` → "Costco"
- `regional_chain` → "Regional Chain"

### Existing endpoint: `POST /api/download/excel`

No changes needed — already accepts `ScenarioInput`, already validates retailer.

## UI design

### Inline validation

Each form field gets a sibling `<span class="field-error" id="<field>-error">`.
The span is empty by default; JS writes to it on validation failure and clears
it on success. The `#form-error` span stays for network/server errors.

CSS addition:
```css
.field-error {
  color: var(--color-red);
  font-size: 13px;
  min-height: 18px;   /* prevents layout shift */
}
```

JS pattern: a `validateField(id, value, message)` helper writes to the
`#<id>-error` span and returns `true/false`. Call before fetch.

### Comparison table

Placed inside `#results-panel`, below the scenario toggle and above the chart.
Hidden until Compare button clicked.

Structure:
```html
<section id="compare-section" class="hidden">
  <h3 class="section-title">Retailer comparison — realistic scenario</h3>
  <table class="compare-table">
    <thead><tr>
      <th>Retailer</th><th>Peak trough</th><th>Break-even</th><th>Net cash Y1</th>
    </tr></thead>
    <tbody id="compare-tbody"></tbody>
  </table>
</section>
```

CSS: follow `.cs-table` pattern from case study. Negative values get
`class="negative"` (red color, already defined as `.negative`).

JS: `renderCompareTable(data)` iterates `data.retailers`, builds rows.
"Compare retailers" button triggers fetch to `/api/compare` with same form
values (no retailer field), then calls `renderCompareTable`.

### Chart hover tooltip

Plotly trace gains `customdata` — a parallel array where each element is
`[gross_revenue[i], deductions[i], cash_received[i]]`.

Updated `hovertemplate`:
```
Month %{x}<br>
Gross revenue: %{customdata[0]:$,.0f}<br>
Deductions: %{customdata[1]:$,.0f}<br>
Cash received: %{customdata[2]:$,.0f}<br>
Cumulative: %{y:$,.0f}
<extra></extra>
```

`renderChart()` already has access to `data.gross_revenue`, `data.deductions`,
`data.cash_received` (these fields are in `ScenarioResult`). No backend change
needed — the frontend just wires them into `customdata`.

## Implementation units

### U1 — Add Costco + Regional chain retailer defaults and dropdown options

**Goal:** New retailers are selectable by the user and flow through the existing
calculate and download endpoints without any other code change.

**Files:**
- Modify: `model/defaults.py` — add `costco` and `regional_chain` entries to `RETAILER_DEFAULTS`
- Modify: `static/index.html` — add two `<option>` elements to the retailer `<select>`

**Approach:**
- Add `"costco"` and `"regional_chain"` dicts to `RETAILER_DEFAULTS` using the
  confirmed values above
- Add `<option value="costco">Costco</option>` and
  `<option value="regional_chain">Regional Chain</option>` after the existing options
- The `retailer_valid` validator in `ScenarioInput` already does
  `if v not in RETAILER_DEFAULTS` — no change needed
- No migration, no schema change

**Test scenarios:**
- `POST /api/calculate` with `retailer="costco"` returns 200 and valid cash flow data
- `POST /api/calculate` with `retailer="regional_chain"` returns 200 and valid cash flow data
- `POST /api/download/excel` with `retailer="costco"` returns 200 and a non-empty response

**Verification:** `pytest tests/test_api.py -k "costco or regional"` passes; existing 54 tests still pass

---

### U2 — New `POST /api/compare` endpoint

**Goal:** A single POST with brand inputs (no retailer) returns a metrics summary
for all four retailers, suitable for populating a comparison table.

**Files:**
- Modify: `app.py` — add `CompareInput` Pydantic model, add `/api/compare` route

**Approach:**
- `CompareInput` is `ScenarioInput` minus `retailer`, with the same field validators
  (copy validators verbatim — DRY is less important here than keeping validation
  self-contained and testable independently)
- Route calls `calculate_scenario(retailer=key, scenario="realistic", **inputs)` for
  each key in `RETAILER_DEFAULTS`
- Catches `ValueError` and returns 422 to match existing endpoint behavior
- Sorts result by `net_cash_impact_year1` descending (best cash position first)
- Maps keys to display labels inside the route (not in `defaults.py`)

**Test scenarios:**
- Valid payload returns 200 with `retailers` array of length 4
- Each entry has `key`, `label`, `trough_value`, `trough_month`, `break_even_month`,
  `net_cash_impact_year1`
- Invalid payload (doors=0) returns 422
- `cogs >= price` returns 422
- `inf`/`nan` velocity returns 422
- Result is sorted best-to-worst by `net_cash_impact_year1`

**Verification:** `pytest tests/test_api.py -k "compare"` passes; existing tests unaffected

---

### U3 — Retailer comparison metrics table UI

**Goal:** A "Compare retailers" button appears in the results panel; clicking it
fetches `/api/compare` with current form values and renders a four-row metrics
table (one row per retailer).

**Files:**
- Modify: `static/index.html` — add compare button + `#compare-section` table skeleton
- Modify: `static/app.js` — add compare fetch handler + `renderCompareTable()`
- Modify: `static/style.css` — add `.compare-table` styles

**Approach:**
- Button placed below the download button, disabled until `currentData` is set
- `renderCompareTable()` builds `<tr>` elements for each retailer entry; negative
  values get class `"negative"` (already defined); no-break-even renders "—"
- Fetch uses same AbortController/timeout pattern as the calculate fetch
- `#compare-section` starts hidden (`display:none`); JS reveals it after first
  successful compare fetch

**Test scenarios (manual):**
- Fill form with valid inputs, click Calculate, then click Compare — table appears
  with four rows
- Negative net cash values render in red
- "—" appears for break_even_month when null
- Table is hidden before Calculate is clicked

**Verification:** Manual test in browser; no automated UI tests added (Plotly/DOM
dependency makes headless testing low-value here)

---

### U4 — Inline per-field validation error spans

**Goal:** Each required input shows its own error message directly below the field
instead of a single page-level error span.

**Files:**
- Modify: `static/index.html` — add `<span class="field-error" id="<field>-error">` after each input
- Modify: `static/app.js` — replace `errorEl.textContent = '...'` with per-field
  `setFieldError(id, message)` calls; clear on valid; keep `#form-error` for
  network/server errors
- Modify: `static/style.css` — add `.field-error` style with `min-height: 18px`
  to prevent layout shift

**Approach:**
- `setFieldError(fieldId, msg)` writes to `#<fieldId>-error`; empty string clears
- `clearFieldErrors()` resets all field-error spans before each validation pass
- Fields with errors: `doors`, `skus`, `unit_price_wholesale`, `cogs_per_unit`,
  `velocity`, and cross-field `cogs_per_unit` (for the cogs >= price case)
- `broker_projection` is optional — only validate if non-empty
- `#form-error` remains for server 4xx/5xx responses

**Test scenarios:**
- Leave doors empty, submit — "Required" appears below doors field only
- Enter cogs >= price — error appears below cogs field
- Correct the error — error span clears before next submit
- Valid full submission — all error spans empty

**Verification:** Manual browser test for each error path; no automated DOM tests added

---

### U5 — Chart hover tooltip with monthly breakdown

**Goal:** Hovering over any point on the cash flow line shows a tooltip with
Gross Revenue, Deductions, Cash Received, and Cumulative cash position for that month.

**Files:**
- Modify: `static/app.js` — add `customdata` to the Plotly trace; update `hovertemplate`

**Approach:**
- In `renderChart(scenario)`, set `customdata` as:
  `data.months.map((_, i) => [data.gross_revenue[i], data.deductions[i], data.cash_received[i]])`
- Update `hovertemplate` to include all four lines (see UI design above)
- No backend change — `gross_revenue`, `deductions`, `cash_received` already in
  `ScenarioResult` and already returned by `/api/calculate`

**Test scenarios (manual):**
- After Calculate, hover a point — tooltip shows all four values
- Switching scenarios (optimistic/realistic/pessimistic) — tooltip values update correctly

**Verification:** Manual browser test; no automated test needed (pure Plotly config)

## Dependencies and sequencing

```
U1 → U2 (U2 calls calculate_scenario; U1 adds the retailers it will iterate)
U1 → U3 (Compare table uses dropdown options from U1)
U2 → U3 (UI calls /api/compare from U2)
U4 independent (pure frontend, no backend change)
U5 independent (pure frontend, already has data from /api/calculate)
```

Recommended order: U1 → U2 → U3, then U4 and U5 in parallel (or serial — both are small).

## Test file targets

- `tests/test_api.py` — new tests for U1 (costco/regional_chain calculate + download)
  and U2 (compare endpoint, validation, sorting)
- `tests/test_calculator.py` — no changes expected
- `tests/test_excel.py` — no changes expected (download endpoint behavior unchanged)

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Costco defaults produce edge case (very low chargeback rate, no slotting) that crashes calculator | Add Costco to integration tests; fix in calculator if it surfaces |
| Per-field validation breaks existing `#form-error` server error display | Keep `#form-error` for network/server errors; field errors are client-side only |
| Compare table layout breaks on mobile | Test at 375px; cap table max-width at `900px` to match content width |
| `customdata` shape mismatch if months array and revenue arrays have different lengths | Both come from the same `ScenarioResult` — identical length by construction |

## Definition of done

- [ ] Costco and Regional chain are selectable and return valid results from `/api/calculate` and `/api/download/excel`
- [ ] `/api/compare` returns a 4-retailer summary for any valid brand inputs
- [ ] Compare table appears in the results panel after clicking "Compare retailers"
- [ ] Each form field shows its own inline error message for invalid input
- [ ] Chart hover tooltip shows monthly breakdown (Gross Revenue, Deductions, Cash Received, Cumulative)
- [ ] All existing tests pass (54/54 baseline)
- [ ] New tests added for U1 and U2 pass
- [ ] Deployed to fly.dev
