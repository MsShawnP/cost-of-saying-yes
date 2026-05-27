# cost-of-saying-yes — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

v2 Excel download: replace hardcoded Cinderhaven defaults with the user's actual scenario inputs. The download button should POST the current form state and stream back a workbook that reflects what the user modeled.

## Why this arc, why now

The Excel download is the primary lead-gen artifact — it's what a CFO would save and share. Right now it always generates Cinderhaven numbers regardless of what the user entered. A CFO who enters their own brand's data and downloads a workbook with someone else's numbers loses trust immediately.

## Tasks

- [x] A1: Convert `/api/download/excel` from GET to POST — accept `ScenarioInput` body (same model as `/api/calculate`), remove hardcoded Cinderhaven values, compute scenarios from user inputs. Keep retailer validation. Update `SecurityHeadersMiddleware` path check to match.
- [x] A2: Update frontend download button — replace `<a href=...>` with a `<button>` and JS handler that POSTs current form state to `/api/download/excel`, receives blob, triggers download via object URL. Reuse existing `payload` from the calculate flow.
- [x] A3: Update `tests/test_api.py` — replace GET-based Excel tests with POST; add assertion that returned workbook reflects posted inputs (e.g., summary sheet row count or a cell value specific to posted door count differs from Cinderhaven default).
- [x] A4: Update README — remove caveat about Excel using hardcoded Cinderhaven defaults.

## Definition of done for this arc

- [x] `pytest` passes — 54/54
- [x] Downloading Excel after entering custom inputs produces a workbook with those inputs' numbers, not Cinderhaven's
- [ ] Download button works end-to-end in the browser
- [ ] Deployed to fly.dev

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.

### 2026-05-27 — Harden test suite and add README (Arc 2)
- Outcome: 45/45 tests passing (up from 28). Fixed vacuous test, added tests/test_excel.py (5 tests) and tests/test_api.py (12 tests), created README.md. No regressions.
- Tag: n/a (no new deployment)

### 2026-05-27 — Ship CFO-credible retailer launch cost model (Arc 1)
- Outcome: Deployed to https://cost-of-saying-yes.fly.dev/ — FastAPI backend, Plotly.js chart with three scenarios, 4-tab openpyxl Excel model, Cinderhaven Walmart case study, 28/28 tests. Followed by /ce:review: 19 safe_auto + 1 gated_auto fix applied; P0 resolved (static/index.html tracked in git).
- Tag: v0.1.0-mvp

---

## Improvement history

Track when this project was reviewed and improved via /improve.
Each entry records what was found, what was fixed, and when to
check again.

<!-- Entries are added by /improve — don't delete this section -->

### 2026-05-27 — Audit (full improve, fixes deferred to Arc 3)
- **Findings:** 1 critical, 6 important, 7 nice-to-have
- **Top concerns:** inf/nan crash path bypasses validators; Excel per-scenario deduction rows render black not red; no fetch timeout for cold-start UX; dev dependencies undeclared
- **Action taken:** Audit complete — all findings written as Arc 3 tasks in PLAN.md. No fixes applied this session.
- **Next review:** 2026-06-27
