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
- [ ] Fix vacuous test: `test_break_even_month_is_positive_if_set` — switch fixture to high-velocity inputs (doors=100, skus=1, price=5.00, cogs=1.00, velocity=20.0, broker=100_000, scenario='optimistic') so the inner assertion actually runs
- [ ] Add `tests/test_excel.py` — 4 tests: (1) workbook has sheets ['Summary','Realistic','Optimistic','Pessimistic'], (2) `workbook_to_bytes()` returns non-empty bytes, (3) Summary cell B2 equals realistic `gross_revenue_year1`, (4) `break_even_month=None` writes fallback string not a Python `None`
- [ ] Add TestClient HTTP integration tests to `tests/test_api.py` — POST /api/calculate with valid body returns 200 with keys realistic/optimistic/pessimistic each with `cumulative_cash_position` length 12; `doors=0` returns 422; GET /api/download/excel returns 200 with correct Content-Disposition and Content-Type; omitting `broker_projection_year1` succeeds

**Documentation**
- [ ] Create `README.md` — what it does (one sentence), how to run locally (`pip install -r requirements.txt && uvicorn app:app --reload`), main tech/stack, live URL

## Out of scope for this arc

- New features
- Frontend changes
- Retailer additions
- Email gating

## Definition of done for this arc

- [ ] `pytest` passes with 0 vacuous tests (verified by checking that the fixed test's assertion branch is actually reached)
- [ ] `tests/test_excel.py` exists with ≥4 meaningful assertions
- [ ] `tests/test_api.py` exists with ≥4 HTTP-level integration tests
- [ ] `README.md` exists and contains: one-sentence description, local run command, stack summary, live URL

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
