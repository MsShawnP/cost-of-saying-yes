# cost-of-saying-yes — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Apply all findings from the 2026-05-27 /improve audit — close the inf/nan crash path, fix the Excel deduction color bug, add a fetch timeout, add dev dependencies, add security headers, add a deduction sign test, and clean up the nice-to-have items.

## Why this arc, why now

The /improve audit found 1 critical crash path (inf/nan bypasses validators), 1 correctness bug in shipped Excel output (monthly deductions render black not red), and 6 other important/polish items. All are small, well-defined fixes. No new features — this arc makes the existing tool correct and defensible.

## Tasks

**Critical**
- [x] C1: Add `math.isfinite()` guard to all float validators in `ScenarioInput` (`app.py`) — price, COGS, velocity — and add upper bounds (doors ≤ 10,000; skus ≤ 100; velocity ≤ 1,000; prices ≤ $10,000). Also add a validator for `broker_projection_year1` (currently unvalidated — accepts negative, zero, `inf`).

**Important**
- [x] I1: Fix Excel per-scenario deduction sign — negate `deductions[m_idx]` when writing column C in `_build_scenario_sheet` (`model/excel.py`) so monthly cost rows render red
- [x] I2: Add fetch timeout + cold-start message — `AbortController` with 30s timeout in `static/app.js`; show "This may take a moment on first load…" message while in-flight
- [x] I3: Add `requirements-dev.txt` with `pytest` and `httpx`; update README test instructions
- [x] I5: Add `SecurityHeadersMiddleware` to `app.py` — `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Cache-Control: no-store` on Excel endpoint
- [x] I6: Add test asserting per-scenario sheet column C (deductions) values are negative — would have caught I1

**Nice to have**
- [x] N1: Move `CINDERHAVEN_INPUTS` fixture to `conftest.py` (project root) — remove duplication from `test_calculator.py` and `test_excel.py`
- [x] N2: Update README — add `ENVIRONMENT=development` note for local dev; add caveat that Excel uses hardcoded Cinderhaven defaults
- [x] N3: Fill in `CLAUDE.md` voice section (currently template placeholder)
- [x] N4: Fix Dockerfile base image from `python:3.12-slim` to `python:3.13-slim`
- [x] N5: Add `[http_service.concurrency]` limit in `fly.toml` to cap parallel requests
- [x] N6: Narrow CORS `allow_methods` from `["*"]` to `["GET", "POST", "OPTIONS"]` in `app.py`
- [x] N7: Fix `scrollIntoView` to fire after Plotly draw; add `prefers-reduced-motion` guard in CSS

## Out of scope for this arc

- New features
- New retailers
- Email gating
- CSP header (breaks Plotly's `unsafe-eval` requirement — skip until Plotly is replaced or bundled differently)
- 422 input-echo strip (P3a from security review — no PII in current schema, defer until schema expands)

## Definition of done for this arc

- [x] `pytest` passes with all new tests (including I6 deduction sign test) — 53/53
- [x] Sending `unit_price_wholesale: Infinity` returns 422, not 500
- [x] Excel per-scenario detail tabs show deduction rows in red
- [x] Calculate button shows cold-start message after 2s; aborts with friendly error after 30s
- [x] `pip install -r requirements-dev.txt && pytest` works on a fresh clone
- [x] Response headers include `X-Frame-Options` and `X-Content-Type-Options`

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
