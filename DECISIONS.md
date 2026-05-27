# cost-of-saying-yes — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-05-26 — Do not start building until problem validation conversation is complete
- **Why:** /office-hours revealed no direct contact with anyone who's lived a major retailer launch. The brief's assumptions (chargeback rates, payment terms, retailer-specific cost parameters, decision-process) need one real conversation to confirm before investing 2-3 weeks of build time. Starting without validation risks building the wrong thing — wrong format, wrong assumptions, wrong primary goal.
- **Scope:** Global — applies to all build work on this project
- **Do not:** Start coding the financial model, UI, or Excel model until the validation conversation has happened and findings are logged in HANDOFF.md.
- **Status:** Resolved — validated by $28M specialty food operator (maple syrup brand). Numbers confirmed credible. Build gates passed.

### 2026-05-26 — Use FastAPI (not Flask) for the Python backend
- **Why:** FastAPI gives automatic API docs, cleaner JSON handling, and less boilerplate than Flask. Flask adds no value for this use case — it's a simple API serving a single-page frontend. FastAPI is the better default for new Python API projects.
- **Scope:** app.py and all backend route definitions
- **Do not:** Use Flask. Do not introduce both — pick one and stay consistent.

### 2026-05-26 — Use Plotly.js (not D3) for the cash flow chart
- **Why:** Plotly.js produces CFO-quality charts out of the box with minimal custom JS. D3 would give more control but adds days of work for marginal visual gain on a solo 2–3 week build. The centerpiece chart is a line chart showing cumulative cash position — Plotly handles this cleanly.
- **Scope:** All charts in the HTML/JS frontend
- **Do not:** Use D3. Do not use Chart.js (insufficient control for the Lailara design system tokens).

### 2026-05-27 — CORS defaults to production-restrictive; development mode requires explicit env var
- **Why:** Inverting the default (from `"development"` fallback to `"production"` fallback) ensures a fresh deploy is never accidentally open. The restrictive allow-list (`["https://cost-of-saying-yes.fly.dev"]`) is active unless `ENVIRONMENT=development` is set explicitly.
- **Scope:** `app.py` CORS configuration. Applies to any future environment-gating in this project.
- **Do not:** Change the `os.getenv("ENVIRONMENT", "production")` default to `"development"` — that would open CORS on every cold deploy where the env var is absent.

---

## Data & Schema

### 2026-05-27 — Walmart defaults back-solved from Cinderhaven validated numbers
- **Why:** `units_per_case = 40` and `chargeback_rate_learning = 0.12` were derived by back-solving from the $28M operator-confirmed fixture, not estimated. Using round-number guesses (4 units/case, 3% chargebacks) produces a trough significantly off from validated numbers.
- **Scope:** `model/defaults.py` — Walmart retailer defaults
- **Do not:** Change these values without re-validating against the Cinderhaven fixture numbers. Do not simplify to 4 units/case or 3% learning chargebacks.

### 2026-05-27 — Return all three scenarios in a single API call
- **Why:** The scenario toggle is a client-side operation — switching optimistic/realistic/pessimistic updates the chart instantly without a server round trip. Computing all three at once is cheap on the server (~3ms); making three sequential requests would be slower and would flash the UI between each switch.
- **Scope:** `POST /api/calculate` response shape and `static/app.js` state model
- **Do not:** Split into three separate endpoints or add a `scenario` parameter to the calculate endpoint. All three come back together, always.

### 2026-05-26 — Python model returns a defined JSON contract to the frontend
- **Why:** The deduction lag model is stateful across months — Month 3's cash receipt depends on Month 1's invoice minus Month 1–2 deductions. Defining the contract before writing frontend code prevents having to reshape the data structure mid-build.
- **Scope:** API response from app.py to index.html
- **Do not:** Start writing frontend chart code before the JSON contract is defined and agreed on. The contract must include at minimum: months array, gross_revenue, cash_received, cumulative_cash_position, break_even_month.

---

### 2026-05-27 — Excel cost rows must be stored as negative numbers in the summary dict
- **Why:** The `neg_currency` openpyxl number format (`"$"#,##0;[Red]("$"#,##0)`) applies red color and parentheses only to numerically negative values. Cost fields stored as positive numbers render in black with no error — the bug is invisible unless you open the workbook. The convention is: positive = inflow, negative = outflow.
- **Scope:** `model/calculator.py` summary dict and `model/excel.py` cost row rendering.
- **Do not:** Store cost fields as `abs()` values and rely on the number format for sign. If adding a new cost line to the summary, negate it at the source in `calculator.py`.

### 2026-05-27 — Shared test constants live in root conftest.py, not tests/conftest.py
- **Why:** pytest adds the rootdir to `sys.path`, not the `tests/` subdirectory. A `conftest.py` inside `tests/` is auto-executed by pytest but not importable as a module — `from conftest import X` raises `ModuleNotFoundError`. The root-level `conftest.py` sits on the same path as `app.py` and `model/`, so imports resolve correctly from all test files.
- **Scope:** All test infrastructure in this project. Applies any time a shared constant or fixture needs to be imported directly (not just auto-used via pytest fixture injection).
- **Do not:** Place importable shared test data in `tests/conftest.py`. It will fail at collection time with a cryptic import error, not at runtime.

### 2026-05-27 — Excel download uses hardcoded defaults, not user form inputs (MVP — resolved in Arc 4)
- **Why:** The download button was an `<a href>` tag — it couldn't POST the current form state to the server.
- **Resolution (Arc 4):** Converted to `POST /api/download/excel` accepting `ScenarioInput` body. Frontend download button now sends current form state via fetch, receives blob, triggers download via object URL.

### 2026-05-27 — Binary file downloads use POST + blob object URL, not anchor href
- **Why:** Anchor `<a href>` can only GET — it can't carry form state. POST body → StreamingResponse → `res.blob()` → `URL.createObjectURL()` is the correct pattern for downloads that depend on user inputs.
- **Scope:** All file export endpoints in this project.
- **Do not:** Add `<a href="/api/download/...">` for any new file export. Always wire a button with a fetch handler.

---

## Visualization

[Chart conventions, palette decisions, interactivity choices]

---

## Output Formats

[Decisions about deliverable formats, structure, organization]

---

## Writing & Voice

[Voice, style, terminology decisions specific to this project]

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
