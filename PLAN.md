# cost-of-saying-yes — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Harden the test suite and document the project — fix a vacuous model test, add Excel workbook tests, add HTTP integration tests via TestClient, and create a README so a fresh clone is usable without digging through code.

## Why this arc, why now

Arc 1 shipped a working tool. The /ce:review identified test gaps that leave the Excel layer and API endpoints untested. The vacuous test gives false confidence. The missing README violates the global CLAUDE.md requirement and means anyone (including future-me) hitting the repo cold has no idea how to run it.

## Business question this arc answers

Is the tool defensible enough to share broadly — does the test suite actually catch regressions in the model, Excel output, and API contract?

## Success metric

All four test gaps resolved. `pytest` passes with meaningful coverage of the Excel workbook, API endpoints, and model edge cases. README exists and is accurate.

## Tasks

**Test hardening**
- [x] Fix vacuous test: `test_break_even_month_is_positive_if_set` — switch fixture to high-velocity inputs (doors=100, skus=1, price=5.00, cogs=1.00, velocity=20.0, broker=100_000, scenario='optimistic') so the inner assertion actually runs
- [x] Add `tests/test_excel.py` — 5 tests: workbook has sheets ['Summary','Realistic','Optimistic','Pessimistic'], `workbook_to_bytes()` returns non-empty bytes, xlsx magic bytes (PK header), Summary cell B2 equals realistic `gross_revenue_year1`, `break_even_month=None` writes fallback string not a Python `None`
- [x] Add TestClient HTTP integration tests to `tests/test_api.py` — 12 tests covering POST /api/calculate (3 scenarios, 12-month arrays, optional broker, whole_foods), validation rejections (doors=0, COGS>price, invalid retailer), Excel download (200, content-type, content-disposition, invalid retailer 422), health endpoint

**Documentation**
- [x] Create `README.md` — what it does (one sentence), how to run locally (`pip install -r requirements.txt && uvicorn app:app --reload`), main tech/stack, live URL

## Out of scope for this arc

- New features
- Frontend changes
- Retailer additions
- Email gating

## Definition of done for this arc

- [x] `pytest` passes with 0 vacuous tests (verified by checking that the fixed test's assertion branch is actually reached)
- [x] `tests/test_excel.py` exists with ≥4 meaningful assertions (5 delivered)
- [x] `tests/test_api.py` exists with ≥4 HTTP-level integration tests (12 delivered)
- [x] `README.md` exists and contains: one-sentence description, local run command, stack summary, live URL

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.

### 2026-05-27 — Ship CFO-credible retailer launch cost model (Arc 1)
- Outcome: Deployed to https://cost-of-saying-yes.fly.dev/ — FastAPI backend, Plotly.js chart with three scenarios, 4-tab openpyxl Excel model, Cinderhaven Walmart case study, 28/28 tests. Followed by /ce:review: 19 safe_auto + 1 gated_auto fix applied; P0 resolved (static/index.html tracked in git).
- Tag: v0.1.0-mvp

---

## Improvement history

Track when this project was reviewed and improved via /improve.
Each entry records what was found, what was fixed, and when to
check again.

<!-- Entries are added by /improve — don't delete this section -->
