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

### 2026-05-27 — Audit (full improve, fixes deferred to Arc 3)
- **Findings:** 1 critical, 6 important, 7 nice-to-have
- **Top concerns:** inf/nan crash path bypasses validators; Excel per-scenario deduction rows render black not red; no fetch timeout for cold-start UX; dev dependencies undeclared
- **Action taken:** Audit complete — all findings written as Arc 3 tasks in PLAN.md. No fixes applied this session.
- **Next review:** 2026-06-27
