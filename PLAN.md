# cost-of-saying-yes — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

No active arc. Tool is complete and deployed.

## Tasks

(none — Arc 7 lead gen push is handled outside Claude Code)

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.

### 2026-07-28 — Tier C findings + chart to bars + first solution doc (Arc 10)
- Outcome: All six Tier C findings closed and deployed. Excel Summary tab now foots
  as a subtraction chain (added Ops Overhead — Year 1 and Uncollected at Year End,
  the latter carrying ~94% of the Year-1 net) and gained Peak Cash Trough / Trough
  Month rows, guarded by a reconciliation test mirroring the API-side one. Breakeven
  display fixed from `toFixed(1)` to `toFixed(2)` — 2.5 was a velocity that loses
  $2,104. Cash-flow chart converted from line to vertical bars, deleting a stride
  helper that silently dropped 7 of 12 labels on mobile; `textangle: -90` plus
  `constraintext: 'none'` keeps every label full-size at every width. Along the way,
  found and fixed a pre-existing production bug: a layout `transition` made
  `Plotly.react` animate instead of re-render, silently skipping annotation updates
  — live since `3fafa25`, undocumented, survived two review passes. Lows: Summary
  tab color, dead style/constant deletion, body text 720px → 660px, and the
  `@media print` block the stylesheet never had. Repo's first `docs/solutions/`
  entry written, `DECISIONS.md` Visualization section filled, `CLAUDE.md` now points
  at the knowledge store. 78/78 tests (up from 76). Deployed and verified on
  production.
- Tag: n/a

### 2026-07-27 — Verdict-first redesign + breakeven-velocity sensitivity (Arc 9)
- Outcome: Live Model tab rewritten to be verdict-first — opens on a "Peak Financing Need vs Broker's Projection" hero card, pre-loads the Cinderhaven example, and recomputes on every input change (no Calculate button). New feature: server-computed breakeven velocity. `POST /api/calculate` now returns a top-level `breakeven_velocity` (lowest velocity at which the realistic scenario's Year-1 net cash ≥ 0, via bisection capped at the model's max velocity; null if it never recovers), rendered as a live one-line sensitivity note in the verdict section. Cinderhaven pins at 2.53 units/door/week (regression-tested at both the model and API layers). Python cash-flow model and formulas untouched. 74/74 tests (up from 66). Deployed.
- Tag: n/a

### 2026-06-23 — Tab restructure + dynamic line-item table (Arc 8)
- Outcome: Page restructured into "Your Model" / "Case Study" tabs. Dynamic line-item table renders user's cost decomposition after Calculate, updates on scenario switch. Source attribution updated for synthetic data disclosure. Case study table corrected (2 missing line items, wrong deduction amount, UNFI label). 66/66 tests (up from 64). Deployed.
- Tag: n/a

### 2026-05-27 — UX polish: retailer context callout, mobile table scroll, flex-wrap (Arc 6)
- Outcome: Per-retailer context callout below dropdown; compare table wrapped in overflow-x:auto (mobile 5-col fix); download section flex-wrap. .claude/launch.json added. 64/64 tests. Deployed.
- Tag: n/a

### 2026-05-27 — New retailers + compare endpoint (Arc 5)
- Outcome: Costco + Regional Chain added to defaults and dropdown. POST /api/compare (4-retailer summary). Compare table UI. Inline per-field validation. Chart hover tooltip with monthly breakdown. 64/64 tests (up from 54). Deployed.
- Tag: n/a

### 2026-05-27 — v2 Excel download: user inputs via POST (Arc 4)
- Outcome: `GET /api/download/excel` (hardcoded Cinderhaven defaults) → `POST /api/download/excel` (accepts `ScenarioInput`). Frontend button converted from `<a href>` to fetch+blob. 54/54 tests. Deployed.
- Tag: n/a

### 2026-05-27 — Harden test suite and add README (Arc 2)
- Outcome: 45/45 tests passing (up from 28). Fixed vacuous test, added tests/test_excel.py (5 tests) and tests/test_api.py (12 tests), created README.md. No regressions.
- Tag: n/a (no new deployment)

### 2026-05-27 — Ship CFO-credible retailer launch cost model (Arc 1)
- Outcome: Deployed to https://launch-cost.lailarallc.com/ — FastAPI backend, Plotly.js chart with three scenarios, 4-tab openpyxl Excel model, Cinderhaven Walmart case study, 28/28 tests. Followed by /ce:review: 19 safe_auto + 1 gated_auto fix applied; P0 resolved (static/index.html tracked in git).
- Tag: v0.1.0-mvp

---

## Improvement history

Track when this project was reviewed and improved via /improve.
Each entry records what was found, what was fixed, and when to
check again.

<!-- Entries are added by /improve — don't delete this section -->

### 2026-07-27 — Improvement pass (full: audit + fix + deploy)
- **Trigger:** User-initiated (improve + code review + UI review, run twice — before and after shipping the verdict-first redesign).
- **What was reviewed:** Python backend, frontend + security, and UI 30-second clarity, via two parallel reviewers plus a manual browser pass.
- **What was fixed:** All 8 findings — breakeven rounded down (2.53→2.54, a real credibility bug), live-recompute response race, sensitivity NaN mis-branch, CSP/HSTS hardening, stale CORS domain, docstring, dedup (`LaunchInputBase` + shared JS fetch helpers + reconciliation guard test), verdict placeholder copy. Two decisions reversed and documented (validator dedup, CSP script-src).
- **Result:** 76/76 tests (was 66 at session start). UI 30-second test now passes. Pushed and deployed; live verified.
- **Deferred:** True single-sourcing of `compute_line_items` (guarded by a reconciliation test, not rewritten).
- **Next review:** 2026-10-25 (stable — 90-day cadence).

### 2026-05-27 — Audit (full improve, fixes deferred to Arc 3)
- **Findings:** 1 critical, 6 important, 7 nice-to-have
- **Top concerns:** inf/nan crash path bypasses validators; Excel per-scenario deduction rows render black not red; no fetch timeout for cold-start UX; dev dependencies undeclared
- **Action taken:** Audit complete — all findings written as Arc 3 tasks in PLAN.md. No fixes applied this session.
- **Next review:** 2026-06-27
