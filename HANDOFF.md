# cost-of-saying-yes — Handoff Log

Session-by-session state. Updated by /log mid-session and /wrap at
session end.

For durable choices, see DECISIONS.md.
For the current work arc, see PLAN.md.
For things that didn't work, see FAILURES.md.

---

## 2026-05-26 — Project initialized

**Started from:** New project setup.

**Did:** Created repo, set up CLAUDE.md/DECISIONS.md/HANDOFF.md/PLAN.md/
FAILURES.md, configured slash commands, ran 95% confidence prompt
in chat.

**State:** Foundation in place. PLAN.md arc defined. Ready to begin
work.

**Next:** Fill in CLAUDE.md stack/voice sections, define first arc in PLAN.md, then run /office-hours and /plan-ceo-review before building.

---

## 2026-05-26 14:00

**What changed:** Ran /office-hours challenge session on the project idea

**Why:** Required step before building — validate the concept has a real problem and a clear goal before committing 2-3 weeks of build time.

**State:** Project is yellow-lit. Idea is solid, brief is sharp, but problem validation is unconfirmed — no direct conversation with anyone who's lived a major retailer launch. Format and primary goal (lead gen vs. portfolio vs. direct sale) also unresolved.

**Next:** Have one 20-minute conversation with a founder/CFO/ops person who's done a Walmart, Costco, or Whole Foods launch. Use the 4 questions from the office-hours session. Then run /plan-ceo-review.

---

## 2026-05-26 — Session wrap

**Started from:** New project, no files existed.

**Did:** Initialized repo + full workflow scaffold. Ran /office-hours challenge. Yellow-lit the project — insight strong, but problem validation unconfirmed and primary goal unresolved.

**State:** Scaffolded and committed. No code. No active PLAN.md arc (intentional — arc should be defined after validation conversation).

**Next:** Have the 20-min validation conversation (4 questions from office-hours). Then run /plan-ceo-review.

---

## 2026-05-27 11:35

**What changed:** Full planning workflow completed — /plan-ceo-review, /plan-eng-review, and /ce:plan all passed. 9-unit implementation plan written.

**Why:** All pre-build gates (validation, CEO review, eng review) cleared. Plan defines the JSON contract, deduction lag model, file structure, and Fly.io deployment approach.

**State:** No code yet. Plan at docs/plans/2026-05-26-001-feat-retailer-launch-cost-model-plan.md is active. 9 tasks created (U1–U9) with dependencies. U1 is unblocked and ready to build.

**Next:** Run /ce:work to start U1 — project scaffold (requirements.txt, app.py skeleton, Dockerfile, fly.toml).

---

## 2026-05-27 12:45

**What changed:** All 9 implementation units built and deployed — tool is live at https://launch-cost.lailarallc.com/

**Why:** Full /ce:work session executed serially U1→U9. Backend (FastAPI + calculator + Excel), frontend (HTML/CSS/JS + Plotly.js + Lailara tokens), and Fly.io deployment all completed in one session.

**State:** 28/28 tests passing. All three scenarios return correct data. Excel download streams a real 4-tab workbook. Cinderhaven case study renders as static HTML. One known gap: model trough falls at month 2, Cinderhaven validated fixture says month 4 — documented in FAILURES.md, not blocking.

**Next:** Open https://launch-cost.lailarallc.com/ and do a manual walkthrough with real inputs. Then run /wrap to close the arc.

---

## 2026-05-27 — Session wrap

**Started from:** Planning complete, no code existed. HANDOFF.md was stale.

**Did:** Built and deployed all 9 implementation units in one session — FastAPI backend (calculator, defaults, Pydantic validation, Excel export), HTML/JS frontend (Lailara design system, Plotly.js chart, scenario toggle, comparison panel), Cinderhaven case study, Fly.io deployment. 28/28 tests passing.

**State:** Live at https://launch-cost.lailarallc.com/. All API endpoints working. Known gap: model trough at month 2 vs. Cinderhaven validated month 4 — documented in FAILURES.md, not blocking. Definition of done 7/8 checked (last box = manual user test).

**Next:** Open the live URL, fill in Cinderhaven inputs (1,200 doors, 4 SKUs, $1.00 wholesale, $0.45 COGS, 2.0 vel), verify chart renders with trough annotation and all three scenarios, verify Excel downloads and opens. If clean, arc is done.

---

## 2026-05-27 — Manual verification confirmed; arc closed

**What changed:** Manual walkthrough confirmed HTML and Excel work. Arc marked complete (8/8 DoD boxes checked, v0.1.0-mvp tagged and pushed).

**Why:** Final verification step from the previous session wrap.

**State:** Live at https://launch-cost.lailarallc.com/. Arc 1 is done.

**Next:** (none — session ended cleanly)

---

## 2026-05-27 — /ce:review completed; 19 safe_auto fixes applied

**What changed:** 12-reviewer code review run; all safe_auto and one gated_auto fix committed and pushed to main.

**Why:** First structured review of the codebase after the initial build sprint.

**State:** 28/28 tests passing. All fixes pushed (commits b0bb3d9, 6398394). P0 resolved: static/index.html is now tracked in git. Key fixes: retailer validation on Excel endpoint, exception handling in API endpoints, CORS default inverted, health check path corrected, resize listener leak fixed, Excel cost rows now render red.

**Next:** Work the P1 manual backlog — fix vacuous test (test_break_even_month_is_positive_if_set), add tests/test_excel.py, add TestClient HTTP integration tests, create README.md, update PLAN.md task boxes and arc history.

---

## 2026-05-27 — Session wrap (post-review)

**Started from:** Arc 1 complete, tool live at https://launch-cost.lailarallc.com/. Manual verification confirmed. Ran /ce:review.

**Did:** 12-reviewer parallel code review. Applied 19 safe_auto fixes + 1 gated_auto fix (Excel cost fields negated so neg_currency format renders red). Resolved P0: static/index.html was never in git (Quarto .gitignore artifact — `*.html` excluded it). CORS default corrected, health check path fixed, resize listener leak patched.

**State:** 28/28 tests passing. All fixes committed and pushed (b0bb3d9, 6398394, 034e218). No broken states. P1 backlog documented and unstarted.

**Next:** Fix vacuous test (`test_break_even_month_is_positive_if_set`), add `tests/test_excel.py` (4 sheets, workbook_to_bytes, cell value, None break-even fallback), add TestClient HTTP integration tests, create README.md, update PLAN.md task boxes and arc history.

---

## 2026-05-27 — Arc 2 complete: test suite hardened, README created

**What changed:** All 4 Arc 2 tasks done — vacuous test fixed, test_excel.py and test_api.py added, README.md created.

**Why:** Post-review P1 backlog. Excel and API layers had zero test coverage; vacuous test gave false confidence; README was missing.

**State:** 45/45 tests passing (was 28). test_calculator.py (28), test_excel.py (5), test_api.py (12). README.md live. All Arc 2 DoD boxes checked. 2 commits unpushed (f5f0b3d, 09957bb).

**Next:** /wrap to close the session, then push.

---

## 2026-05-27 — Session wrap (Arc 2 complete)

**Started from:** Post-review /wrap partially complete (compacted mid-session). Arc 1 done, Arc 2 defined.

**Did:** Completed the previous /wrap (HANDOFF, FAILURES, DECISIONS, PLAN.md arc archive). Ran /ce:work for all 4 Arc 2 tasks: fixed vacuous test, added tests/test_excel.py (5 tests), added tests/test_api.py (12 tests), created README.md.

**State:** 45/45 tests passing. README.md live. Arc 2 fully done (all DoD boxes checked). No broken states.

**Next:** Arc 2 is done. Define Arc 3 — options: UX polish (fetch timeout/cold-start messaging, scrollIntoView fix), or run /improve for a full audit, or start sharing the tool toward the 90-day lead gen goal.

---

## 2026-05-27 — /improve audit run; 14 findings across all severity levels

**What changed:** Full /improve audit completed — manual health check + security review + code quality review run in parallel.

**Why:** Scheduled post-arc health check; recommended as next step after Arc 2.

**State:** No fixes applied yet. 45/45 tests passing. 1 critical finding (inf/nan crash path), 6 important findings, 7 nice-to-have. All findings logged in PLAN.md as Arc 3 tasks.

**Next:** New session — run /ce:work to execute all Arc 3 fixes (C1 inf/nan + upper bounds, I1 Excel deduction sign, I2 fetch timeout, I3 dev requirements, I5 security headers, I6 deduction test, N-items).

---

## 2026-05-27 — Session wrap (/improve audit)

**Started from:** Arc 2 complete, no active arc. /next recommended /improve.

**Did:** Ran /improve as scheduled health check — manual audit + security review in parallel. 14 findings: 1 critical (inf/nan crash), 6 important, 7 nice-to-have. Wrote all findings as Arc 3 tasks in PLAN.md.

**State:** 45/45 tests passing. No fixes applied — audit only. Arc 3 fully defined and ready to execute.

**Next:** New session → /ce:work on Arc 3. Start with C1 (inf/nan + upper bounds, `app.py`) and I1 (Excel deduction sign, `excel.py`).

---

## 2026-05-27 — Arc 3 complete: all audit findings resolved

**What changed:** All 13 Arc 3 tasks executed — C1 (critical inf/nan crash path), I1–I6 (all important fixes), N1–N7 (all nice-to-haves).

**Why:** Full /ce:work pass on the /improve audit findings. Tool is now correct, defensible, and hardened for CFO-credible use.

**State:** 53/53 tests passing (was 45). No broken states. Committed (d404a8c, 1517c9b), not yet pushed. Arc 3 all DoD boxes checked in PLAN.md.

**Next:** Push to origin/main. Then define Arc 4 or share the live tool toward the 90-day lead gen goal.

---

## 2026-05-27 — Session wrap (Arc 3 complete)

**Started from:** Arc 3 fully defined, 45/45 tests, no fixes applied — audit only from previous session.

**Did:** Executed all 13 Arc 3 tasks in one /ce:work pass: C1 (inf/nan crash path closed), I1 (Excel deduction sign fixed), I2 (fetch timeout + cold-start hint), I3 (requirements-dev.txt), I5 (security headers middleware), I6 (deduction sign test), N1–N7 (conftest refactor, README, CLAUDE.md voice, Dockerfile, fly.toml, CORS narrowing, scrollIntoView + prefers-reduced-motion). Added 8 new validation tests.

**State:** 53/53 tests passing. All Arc 3 DoD boxes checked. 3 unpushed commits on main. No broken states.

**Next:** Push to origin/main → `fly deploy` to update the live tool → define Arc 4 (share the tool for lead gen, or v2 Excel download that uses user inputs instead of hardcoded Cinderhaven defaults).

---

## 2026-05-27 — Arc 4 in progress: Excel download converted to POST with user inputs

**What changed:** `/api/download/excel` converted from GET (hardcoded Cinderhaven defaults) to POST (accepts `ScenarioInput` body). Frontend download button now POSTs current form state, receives blob, triggers download via object URL. 54/54 tests passing.

**Why:** Excel was the primary lead-gen artifact but always generated Cinderhaven numbers regardless of user inputs — a CFO entering their own brand's data would get someone else's workbook.

**State:** 54 tests passing. Arc 4 tasks A1–A3 done (committed 670d0e8). A4 open: README still has the hardcoded-defaults caveat that no longer applies. Not yet deployed.

**Next:** Remove Excel hardcoded-defaults caveat from README (A4), commit, `fly deploy`, then /wrap.

---

## 2026-05-27 — Session wrap (Arc 4 complete)

**Started from:** Arc 3 deployed. Next: push Arc 3, fly deploy, then define Arc 4.

**Did:** Pushed Arc 3, deployed. Defined and executed Arc 4 in full: converted `/api/download/excel` from GET with hardcoded Cinderhaven defaults to POST accepting `ScenarioInput`; updated frontend download button to fetch-POST with blob download; updated tests (GET→POST, added workbook-reflects-inputs assertion); removed README caveat. Deployed Arc 4 to fly.dev.

**State:** 54/54 tests passing. Arc 4 fully deployed at https://launch-cost.lailarallc.com/. No broken states. Excel download reflects user inputs.

**Next:** Arc 4 done. Define Arc 5 — options: (1) share the tool for lead gen (LinkedIn post, CFO/operator outreach); (2) UX polish; (3) new retailer.

---

## 2026-05-27 — Session wrap (Arc 5 planned)

**Started from:** Arc 4 complete and deployed. Arc 5 options listed in PLAN.md but not defined.

**Did:** Selected Arc 5 scope (UX polish + new retailers). Confirmed Costco + Regional chain defaults. Ran `/ce:plan` — wrote full 5-unit plan to `docs/plans/2026-05-27-001-feat-arc5-retailers-ux-plan.md`. No code changed.

**State:** 54/54 tests passing. Plan written and ready. Arc 5 not started. Baseline unchanged.

**Next:** New session → `/ce:work` on `docs/plans/2026-05-27-001-feat-arc5-retailers-ux-plan.md`. Order: U1 (defaults + dropdown) → U2 (compare endpoint) → U3 (compare table) → U4 + U5 (inline validation + chart tooltips).

---

## 2026-05-27 18:03

**What changed:** Arc 5 complete — Costco + Regional Chain retailers, compare endpoint, comparison table UI, inline field validation, chart hover tooltips.

**Why:** Full `/ce:work` pass on the Arc 5 plan. All 5 units shipped in one session.

**State:** 64/64 tests passing (up from 54). All 5 DoD boxes checked. Deployed to https://launch-cost.lailarallc.com/. Live smoke test confirmed: Costco, Regional Chain, Whole Foods, and Walmart all return valid results from `/api/compare`.

**Next:** Run `/wrap` to close the session. Then decide Arc 6 — share the tool for lead gen (LinkedIn, CFO outreach) or add more UX polish.

---

## 2026-05-27 18:03 — Session wrap (Arc 5 complete)

**Started from:** Arc 5 fully planned, no code written. 54/54 tests. Previous session ended after `/ce:plan`.

**Did:** Executed all 5 Arc 5 units in one `/ce:work` pass — Costco + Regional Chain defaults and dropdown (U1), `POST /api/compare` endpoint with `CompareInput` model (U2), comparison table UI with Compare Retailers button (U3), per-field inline validation error spans (U4), chart hover tooltip with monthly breakdown via Plotly customdata (U5). Deployed to fly.dev. Live smoke test confirmed.

**State:** 64/64 tests passing. Arc 5 fully deployed at https://launch-cost.lailarallc.com/. No broken states. 0 unpushed commits.

**Next:** Arc 5 done. Define Arc 6 — options: (1) share the tool for lead gen (LinkedIn post, CFO/operator outreach — the 90-day goal); (2) UX polish (mobile table layout, Costco-specific copy). Tool is CFO-credible enough to share now.

---

## 2026-05-27 18:30

**What changed:** Arc 6 UX polish — retailer context callout, mobile compare table scroll, download section flex-wrap.

**Why:** Mobile compare table overflowed with 5 columns; no per-retailer copy made Costco's distinct economics invisible to the user.

**State:** 64/64 tests passing. All three changes committed (ac9aeb9). Deploying to fly.dev now.

**Next:** Deploy Arc 6 to fly.dev, then define Arc 7 — lead gen push (LinkedIn post, CFO outreach).

---

## 2026-05-27 18:35 — Session wrap (Arc 6 complete)

**Started from:** Arc 5 complete and deployed. Arc 6 not yet defined.

**Did:** Arc 6 UX polish — per-retailer context callout below dropdown, overflow-x scroll wrapper on compare table (5-col mobile fix), flex-wrap on download section. Created .claude/launch.json for preview_start. Logged, deployed, pushed.

**State:** 64/64 tests passing. Arc 6 deployed at https://launch-cost.lailarallc.com/. origin/main current. PLAN.md shows Arc 5 as active — needs Arc 6 archived and Arc 7 defined.

**Next:** Define Arc 7 — lead gen push. LinkedIn post targeting CPG founders/CFOs + DM 5–10 operators who've done a Walmart or Costco launch.

---

## 2026-05-27 19:04

**What changed:** CE review complete — 9 findings (1 P1, 6 P2, 2 P3), all safe_auto fixes deferred to tomorrow

**Why:** Post-Arc-6 structured review. Pre-compaction P0 claim (CompareInput.effective_broker_projection missing) was a false positive — method exists at app.py:201. Re-verified from source.

**State:** 64/64 tests passing. No fixes applied — review only. Findings: #1 no exception logging (P1); #2 RETAILER_LABELS KeyError risk; #3 Excel fetch no timeout; #4 !value falsy check; #5 compare no cold-start hint; #6 style.display inconsistency; #7 broker no upper bound; #8 no CSP (manual); #9 module-level DOM access (advisory).

**Next:** New session → apply all safe_auto fixes (#1–#7), then define Arc 7 (lead gen push).

---

## 2026-05-27 19:08 — Session wrap (CE review complete)

**Started from:** Arc 6 deployed. CE review interrupted mid-synthesis by context compaction; artifact directory empty on resume.

**Did:** Resumed CE review synthesis. Verified pre-compaction P0 (CompareInput.effective_broker_projection missing) was a false positive — method exists at app.py:201. Re-reviewed diff from source. Produced 9-finding report: 1 P1 (no exception logging), 6 P2 (RETAILER_LABELS KeyError risk, Excel fetch no timeout, !value falsy check, compare no cold-start hint, style.display inconsistency, broker no upper bound), 2 P3 (no CSP, module-level DOM access). All fixes deferred to next session.

**State:** 64/64 tests passing. No code changed this session — review only. 1 unpushed commit (dd2aa54, /log entry).

**Next:** New session → apply safe_auto fixes #1–#7 in one pass, then define Arc 7 (lead gen push).

---

## 2026-05-28 10:07 — Session wrap (all CE review fixes applied + deployed)

**Started from:** CE review complete, 9 findings documented, no fixes applied yet.

**Did:** Applied all 9 CE review fixes in one /ce:work pass — exception logging, RETAILER_LABELS fallback, broker upper bound, Excel fetch AbortController, isNaN() field checks, compare cold-start hint, compare-section classList toggle, CSP header, DOMContentLoaded guard. 64/64 tests. Pushed and deployed to Fly.io.

**State:** 64/64 tests passing. All CE review findings resolved. Deployed at https://launch-cost.lailarallc.com/. No open findings. Arc 7 not started.

**Next:** Arc 7 — lead gen push. No code needed. Draft LinkedIn post + direct outreach to 5–10 CPG founders/operators. Tool is ready to share.

---

## 2026-06-23 16:45

**What changed:** Restructured page into two tabs (Your Model / Case Study) with dynamic line-item table that decomposes user inputs after Calculate.

**Why:** Calculator output showed only a chart and summary numbers — no line-item visibility into where the costs come from. Case study was always visible, cluttering the model tab. Now users see their own cost breakdown, and the Cinderhaven case study lives on its own tab.

**State:** 66/66 tests passing. Deployed to Fly.io. compute_line_items() in app.py, renderLineItems() in app.js, tab CSS in style.css, restructured index.html. Cache busters (?v=2) on CSS/JS tags. All working — dynamic table updates on scenario switch.

**Next:** Run /wrap to close the session.

---

## 2026-06-23 17:00 — Session wrap

**Started from:** Arc 6 deployed, all CE review fixes applied. Arc 7 (lead gen) was next defined goal. No code tasks queued.

**Did:** Three changes in one session: (1) updated Cinderhaven source attribution to disclose synthetic data, (2) fixed case study table (added Ops Overhead + Cash Collection Lag, corrected Ongoing Deductions $4,992→$3,744, renamed UNFI dropdown label), (3) restructured page into two tabs with dynamic line-item table showing user's cost decomposition. All three committed, pushed, deployed to Fly.io.

**State:** 66/66 tests passing. Deployed. Both tabs working — Your Model shows dynamic line-item table that updates on scenario switch, Case Study shows static Cinderhaven data. All numbers verified correct (−$36,320 net cash impact).

**Next:** Arc 7 — lead gen push. Draft LinkedIn post + direct outreach to 5–10 CPG founders/operators. Tool is CFO-credible and ready to share.

---

## 2026-07-27 — Verdict-first redesign shipped + breakeven-velocity feature

**What changed:** Shipped the uncommitted verdict-first front-end redesign (hero card that opens on "Peak Financing Need vs Broker's Projection," pre-loaded Cinderhaven example, live recompute on every input change — no Calculate button). Added a breakeven-velocity sensitivity feature: `calculate_breakeven_velocity()` in `model/calculator.py` bisects for the lowest velocity where the realistic scenario's Year-1 net cash ≥ 0 (capped at MAX_VELOCITY=1000, returns None if it never recovers); `POST /api/calculate` returns it as a top-level `breakeven_velocity` field; `updateSensitivity()` in `app.js` renders a live one-line note in the verdict section phrased against the current velocity. Regression pins added at model level (`test_calculator.py`) and API level (`test_api.py`).

**Why:** Redesign surfaces the CFO answer in under 30 seconds. The sensitivity line answers the obvious follow-up — "how much better does velocity have to be to not lose money?" — with a model-computed number, not a hardcoded one.

**State:** 74/74 tests passing (was 66). Verified locally against a fresh server — trough −156,352, net −36,320, broker 499,200, breakeven_velocity 2.53. Both note branches confirmed live in-browser. Deployed to Fly.io.

**Next:** (none — feature complete; back to Arc 7 lead-gen when ready).

---

## 2026-07-27 — Code-review sweep: all 8 findings fixed

**What changed:** Re-ran /improve + code review + UI review on the shipped redesign, then fixed all 8 findings. Two were real bugs in the just-shipped feature: (1) `calculate_breakeven_velocity` rounded the crossover DOWN, reporting 2.53 where the model still nets −$51 — now ceils to the nearest cent (2.54, which nets +$633); (2) the live-recompute flow had a response race — a slow `/api/calculate` reply could overwrite a fresher one — now gated by a monotonic `calcSeq` id. Also: (3) `updateSensitivity` mis-branched on an empty velocity box (`x > NaN` is always false); (4) CSP tightened (`script-src 'self'`, dropped dead cdn.plot.ly, added base-uri/object-src) + HSTS header; (5) CORS allowlist adds launch-cost.lailarallc.com; (6) breakeven docstring corrected (affine, not monotonic); (7) dedup — `LaunchInputBase` shared model (−90 lines, reverses the 2026-05-27 keep-separate decision), shared `buildPayload`/`parseErrorDetail`/`timedFetch` JS helpers, and a line-items↔net-cash reconciliation guard test; (8) verdict placeholder copy aligned to the live text.

**Why:** UI 30-second test now passes (the redesign fixed it); these were the correctness/robustness/hardening items the two reviewers surfaced. The breakeven rounding bug and the response race both undermined the "numbers you can trust" promise.

**State:** 76/76 tests passing (was 74). All flows verified live in-browser — calculate/compare/download all 200, Plotly renders under tightened CSP, security headers confirmed, both sensitivity-note branches + the NaN branch correct. Committed on main. NOT yet deployed — live site still serves 2.53; needs `fly deploy` to correct it. DECISIONS.md updated for the two reversed decisions (validator dedup, CSP script-src).

**Next:** `fly deploy` to push the breakeven fix (2.53→2.54) and hardening live, then verify.

---

## 2026-07-27 — Session wrap

**Started from:** Tool complete/deployed (Arc 8), no active arc. Asked to run improve + code review + UI review.

**Did:** Ran the review sweep, shipped the verdict-first redesign + a new breakeven-velocity sensitivity feature, re-reviewed, then fixed all 8 findings (two real bugs of my own: breakeven rounding down, live-recompute response race). Pushed and deployed both changesets.

**State:** 76/76 tests. Live at launch-cost.lailarallc.com — breakeven 2.54, HSTS + tightened CSP confirmed, Plotly renders. `origin/main` at `69e34cf` (before this wrap commit). No broken states.

**Next:** Code done and shipped. Real next work is Arc 7 — lead-gen push (LinkedIn + operator outreach), no code. Optional follow-up: true single-sourcing of `compute_line_items` (currently a reconciliation-test guard, not a rewrite).

---

## 2026-07-28 — Tier C review: 6 findings fixed, deployed

**What changed:** Worked a 6-item Tier C finding list end to end.

1. **Critical — the Excel Summary tab did not foot.** It reads as a subtraction
   chain but was missing two rows entirely: Ops Overhead — Year 1 ($38,784) and
   Uncollected at Year End ($34,112). Net Revenue less Upfront less COGS came to
   **+$36,576** against a stated **−$36,320**. Both figures are now computed in
   `calculator.py` (`ops_overhead_year1`, `uncollected_at_year_end`, negated per
   the cost-row convention) and rendered between COGS and Net Cash Impact.
2. **High — `app.js` re-rounded the breakeven with `toFixed(1)`**, displaying
   "2.5" where the API returns 2.54. 2.5 nets −$2,104 — it threw away the exact
   guarantee the `math.ceil` in `calculate_breakeven_velocity` exists to provide.
   Now `toFixed(2)`.
3. **Medium — cash-flow chart had no data labels** (Lailara rule: every data
   point gets one). Added `lines+markers+text`.
4. **Medium — Summary tab gains Peak Cash Trough and Trough Month rows**, read
   from the root of the scenario result via a new `_metrics()` helper. The None
   fallback is now keyed to `break_even_month` instead of firing on any None
   (with more rows, a missing key would have silently printed "No break-even in
   12 months" in a currency cell).
5. **Low — Summary sheet tab colored Chicago navy**; deleted the unused `CANVAS`
   constant and the registered-but-never-applied `sub_header` style (and
   `LIGHT_GRAY`, which only `sub_header` used).
6. **Low — body text capped at the DS 660px** (was 720px in two places) and the
   `@media print` block the file never had: US Letter at 0.6in, white canvas,
   interactive chrome hidden, both tab panes printed, repeating table headers,
   `print-color-adjust` on the verdict card so its inverted panel doesn't print
   white-on-white.

**Why the chart work grew:** verifying finding 3 surfaced two problems. Twelve
labels collide below ~560px of chart width, so `buildPointLabels()` drops to
every third month plus the last on narrow viewports and the resize listener now
re-renders instead of only calling `Plots.resize` (the stride depends on width).
More seriously, the layout `transition` made `Plotly.react` **animate instead of
re-render, silently skipping structural updates** — annotations kept their old
text, so the trough callout showed a stale figure and the break-even marker
never appeared on live recompute. Pre-existing since the verdict-first redesign,
but the new labels put the stale number right next to the fresh one. Removed the
transition (cost: the 350ms ease between scenario switches). Also moved the
trough callout below its point — above is where the point's own label goes.

**State:** 78/78 tests (was 76). Two new Excel tests: a Summary-chain
reconciliation guard mirroring `test_api.py::test_line_items_reconcile_to_net_cash`,
and a trough-row wiring test. `origin/main` at `fafff5e`. Deployed and verified
live: `breakeven_velocity` 2.54, trough −156,352 at month 1, Summary tab foots
for all three scenarios, `app.js?v=10` / `style.css?v=4` serving from the edge.
Layout measured in-browser — 12 labels with zero overlaps at 1440px, 5 at 375px,
annotations track scenario switches and the resize round-trip.

**Next:** No open code work. Arc 7 (lead-gen) is still the real next step. Note
for a future session: `.cs-table` markup on the Case Study tab hardcodes the
Cinderhaven line items in HTML while the Live Model tab renders them from
`compute_line_items` — the two could drift.

> **Superseded below (same day).** The chart described in this entry as a line
> chart with per-point labels and a width-dependent label stride was replaced by
> a vertical bar chart later the same session. See the 2026-07-28 bar-chart entry.

---

## 2026-07-28 — Chart to bars; first solution doc; all Tier C work live

**What changed:** Three commits after the Tier C fixes, all now deployed.

**1. Cash-flow chart converted to vertical bars (`8e76a91`).** The earlier entry's
line chart carried per-point labels via a `buildPointLabels()` stride helper that
dropped 7 of 12 labels below ~560px — an undocumented exception to the design
system's "every data point gets a text label" rule, hidden inside a function.
Bars are the DS default for a time series and remove the constraint instead of
working around it. `buildPointLabels()` and the width-dependent resize re-render
are both gone; the resize handler is back to a plain `Plots.resize`.

**The non-obvious part:** bars did **not** fix mobile for free. At 375px Plotly
rendered all 12 labels with zero overlaps — by scaling them to `scale(0.446)`,
roughly 5px. The bounding-box collision check reported clean. It was measuring
position and saying nothing about legibility. `textangle: -90` is what actually
creates the room; `constraintext: 'none'` only stops Plotly from concealing the
shortfall by shrinking. Do not remove either.

Two knock-on fixes the conversion forced: the boxed trough callout became a plain
"Peak trough" caption (the box repeated a figure the bar now prints itself, and
the verdict card states it a third time), and the break-even caption moved to
paper coordinates after it collided with the month-12 label on a late break-even.

**2. First `docs/solutions/` entry (`b04d332`).** `ce-compound` full run —
`docs/solutions/ui-bugs/plotly-silent-render-failures-2026-07-28.md`. Covers both
Plotly defects (the `transition`-skips-structural-updates bug and the text-shrink
trap) plus two investigation traps: you cannot test a diff-based renderer by
handing it back its own object, and a geometric assertion says nothing about
legibility. `DECISIONS.md` Visualization was an empty placeholder and now holds
two entries with explicit Do-nots, written in the same commit as the doc.

The `component` frontmatter field is deliberately omitted — the ce-compound enum
is Rails-specific and `frontend_stimulus` would have been misleading in this
repo's first solution doc. Reasoned in a note at the foot of the doc. The schema
lives in the plugin cache and is overwritten on update, so fixing the enum
properly is an upstream change.

**3. `CLAUDE.md` now points at `docs/solutions/` (`823c47e`).**

**State:** 78/78 tests. `origin/main` at `823c47e`, working tree clean, deployed
and verified on production — trace type `bar`, 12 bars, 12 labels at `scale 1.0`,
zero overlaps, nothing out of bounds, trough −$156,352, sensitivity 2.54. Verified
by measuring rendered node geometry across velocity 2.0 / 2.6 / 4.0 / 12.0 and all
three scenarios at 1440px and 375px, not by eye.

**Next:** No open code work; every Tier C finding is closed and live. Arc 7
(lead-gen) remains the real next step. Two things a future session should know:
the Case Study tab's hardcoded `.cs-table` markup can still drift from
`compute_line_items` (unchanged from the entry above), and the render assertion
in the solution doc is a manual `/qa` check — there is no JS test runner in this
repo, so nothing in CI would catch a recurrence.

---
