# cost-of-saying-yes — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Ship a CFO-credible, interactive retailer launch cost model — HTML/JS frontend + Python backend — with a Cinderhaven Walmart case study, downloadable Excel model, and a month-by-month cash flow chart that makes the revenue-vs-cash-reality gap impossible to ignore.

## Why this arc, why now

This is the only active project. Problem validated by a $28M specialty food operator. Stack decided. All planning gates passed. Time to build.

## Business question this arc answers

For a $3M–$20M specialty food brand considering a major retailer: what does saying yes actually cost in the first 12 months, and when does the investment break even?

## Success metric

In 90 days: at least 3 inbound inquiries referencing the tool, OR at least 1 Retailer Launch Economics engagement ($5K–$15K) directly attributed to it.

## Tasks

Work in vertical slices — one feature end-to-end before moving to the next.

**Slice 1 — Core financial model (Python)**
- [ ] Define JSON contract: what the Python model returns to the frontend (months, gross_revenue, cash_received, cumulative_cash_position, break_even_month) — do this before any frontend work
- [ ] Build month-by-month cash flow model engine in Python: invoice generation, payment terms lag, deduction netting (trade spend, chargebacks, slotting), ops overhead
- [ ] Implement deduction lag correctly: decouple invoice date from cash receipt date (60–90 day gap with netting)
- [ ] Add input validation: guard against velocity=0, COGS > price, negative inputs, missing required fields
- [ ] Add retailer parameter defaults: Walmart and Whole Foods/UNFI to start
- [ ] Validate Cinderhaven numbers: 4 SKUs, 1,200 Walmart doors, realistic velocity and cost inputs from the brief
- [ ] Write unit tests for core calculation: gross revenue, deductions, net cash, break-even month

**Slice 2 — HTML/JS frontend**
- [ ] Build single-page app: input form (retailer, doors, SKUs, price, COGS, velocity) + results panel
- [ ] Implement month-by-month cumulative cash flow chart (Plotly or D3) — the centerpiece visual
- [ ] Add three-scenario toggle: optimistic / realistic / pessimistic
- [ ] Add "revenue projection vs. cash reality" comparison panel — the killer insight
- [ ] Apply Lailara design system: canvas background, Chicago navy, HK teal, Playfair/Source Sans 3

**Slice 3 — Excel model**
- [ ] Build CFO-grade Excel via openpyxl: scenario tabs, sensitivity analysis (velocity + deduction rate), formatted for board presentation
- [ ] Wire Excel download button in the frontend

**Slice 4 — Cinderhaven case study**
- [ ] Write the Walmart case study narrative using validated numbers
- [ ] Render as a static section below the interactive tool

**Slice 5 — Polish and deploy**
- [ ] Mobile responsiveness
- [ ] Deploy to Fly.io (or equivalent)
- [ ] Smoke test end-to-end from fresh URL

## Out of scope for this arc (v2)

- Costco-specific mode (dynamic UI, pallet/rotation inputs, rotation cliff scenario)
- UNFI/KeHE distributor toggle (double cash conversion hit, distributor margin)
- Board-ready PNG slide export
- Additional retailers beyond Walmart and Whole Foods
- Email gating for Excel download
- Integration with Retail Readiness Scorecard

## Definition of done for this arc

- [x] Core model calculates month-by-month cash flow correctly — deduction lag decoupled from invoice date
- [x] Cinderhaven Walmart scenario matches the validated numbers from brief (within 6.5% on trough; discrepancy documented in FAILURES.md)
- [x] Chart renders cleanly and shows the cash trough and break-even month
- [x] Three scenarios work and produce meaningfully different outputs
- [x] Excel downloads and is formatted well enough to hand to a CFO
- [x] Unit tests pass for the calculation engine (28/28)
- [x] Deployed and accessible at a public URL — https://cost-of-saying-yes.fly.dev/
- [ ] Someone other than you can use it without explanation

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.

### [Date completed] — [Goal]
- Outcome: [what shipped or what was decided]
- Tag: [git tag if one was created]

---

## Improvement history

Track when this project was reviewed and improved via /improve.
Each entry records what was found, what was fixed, and when to
check again.

<!-- Entries are added by /improve — don't delete this section -->
