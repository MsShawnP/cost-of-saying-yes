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

---

## Data & Schema

[Decisions about data sources, schemas, transformations]

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
