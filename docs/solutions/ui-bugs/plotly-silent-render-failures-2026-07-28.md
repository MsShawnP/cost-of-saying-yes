---
title: Plotly renders that look correct and are not
date: 2026-07-28
category: ui-bugs
module: static/app.js — cumulative cash flow chart
problem_type: ui_bug
severity: high
symptoms:
  - "Trough callout kept a previous input's dollar figure while the verdict card above it showed the current one"
  - "A newly-applicable break-even annotation never appeared, though it was present in gd.layout.annotations"
  - "Widening the viewport left 5 of 12 point labels in the DOM while gd.data[0].text held all 12"
  - "Bar labels at 375px rendered at scale(0.446) — about 5px — passing a bounding-box collision check while being unreadable"
  - "No console error, no warning, no rejected promise, in any of the above"
root_cause: wrong_api
resolution_type: code_fix
tags:
  - plotly
  - plotly-react
  - layout-transition
  - stale-annotations
  - silent-failure
  - chart-rendering
  - dom-verification
  - data-correctness
---

# Plotly renders that look correct and are not

## Problem

Two separate defects in the same chart, weeks apart, with one shared shape: Plotly
accepted correct state, returned a resolved promise, raised nothing, and put
something else on screen. On a tool whose entire premise is that a CFO can trust
the figures, the chart displayed a stale trough number beside a fresh one.

## Symptoms

**Defect 1 — `Plotly.react` skipped structural updates.** The layout carried
`transition: { duration: 350, easing: 'cubic-in-out' }`. With a layout transition
present, `react` routes through Plotly's animation machinery instead of its redraw
path. That machinery interpolates attributes of elements that *already exist*; it
cannot create elements that were not there when the tween started.

- The `Peak trough` annotation kept its previous text. `gd.layout.annotations[n].text`
  held the new string; the rendered `.annotation-text` node did not.
- A break-even annotation that became applicable never rendered at all — no node
  to tween from.
- After per-point labels were added, resizing narrow → wide left 5 text nodes while
  `gd.data[0].text` correctly held 12 non-empty strings. The 5 existing nodes had
  their content updated; the 7 absent ones were never created.

Trace *values* animated correctly the whole time, which is exactly why this
survived two code-review passes and weeks in production. The chart looked alive.

**Defect 2 — Plotly silently shrank bar text to fit.** After converting to a bar
chart, `textposition: 'outside'` labels at 375px rendered with
`transform="… scale(0.4459…)"` — 11px declared, ~5px actual. Plotly's default
`constraintext` behavior shrinks outside bar text until it fits the bar width
rather than letting it overflow.

This one is worse than it sounds, because it defeated the verification method:
a bounding-box overlap check reported **zero collisions**. The labels did not
overlap. They were also unreadable. The check measured the right property and
drew the wrong conclusion.

## What Didn't Work

**Waiting for a symptom.** Neither defect ever announced itself. No console error,
no network anomaly, no rejected promise. Defect 1 only became visible when a
second feature — per-point labels — put a freshly computed number physically
beside a stale one inside the same chart. The feature made the older bug legible;
nothing about the bug itself changed.

**Testing `Plotly.react` by handing it Plotly's own object.**

```js
// INVALID — proves nothing
Plotly.react(gd, [gd.data[0]], gd.layout, config);
```

`gd.data[0]` is the object Plotly already holds. `react` diffs incoming against
stored, sees the same reference with identical contents, correctly no-ops. The
test "passed" and was worthless — a healthy and a broken `react` produce the same
result. **Any diff-based renderer is untestable via its own state.** The valid
probe has to construct a genuinely new object graph:

```js
const t = { ...gd.data[0], text: [...gd.data[0].text] };
const l = JSON.parse(JSON.stringify(gd.layout));
delete l.transition;
Plotly.react(gd, [t], l, config);   // → 12 nodes;  with l.transition → 5
```

**A workaround that worked but was rejected.**
`Plotly.relayout(gd, { annotations: gd.layout.annotations })` after each `react`
does force correct annotation text into the DOM. It is a second render pass
papering over the first, it does nothing for missing trace text nodes, and it
would have to be remembered at every future call site.

**Counting overlaps as a proxy for legibility.** See Defect 2. Zero overlaps was
true and meaningless. The check needed a second assertion — that no label had been
scaled below its declared size — which did not exist until the shrink was found by
reading a `transform` attribute for an unrelated reason.

## Solution

**Defect 1** — remove `transition` from the layout, with a comment at the deletion
site so it is not reintroduced as polish:

```js
  return {
    paper_bgcolor: '#f5f3ee',
    // NO `transition` here. A layout transition makes Plotly.react animate the
    // existing DOM instead of re-rendering it, and it silently skips structural
    // updates — annotations keep their old text, so the trough caption and the
    // break-even marker would describe a chart the reader is no longer looking at.
    // Correct numbers beat a 350ms ease.
    xaxis: { /* … */ },
```

Trade-off accepted: scenario switches now snap instead of easing.

**Defect 2** — disable the shrink and rotate the labels upright, so every bar keeps
a full-size label at every width:

```js
    type: 'bar',
    text: data.cumulative_cash_position.map(v => formatCurrency(v)),
    textposition: 'outside',
    textangle: -90,
    constraintext: 'none',
    textfont: { family: 'Source Sans 3, sans-serif', size: 11, color: '#333333' },
    cliponaxis: false,
```

Rotation is what actually creates the room. `constraintext: 'none'` only stops
Plotly from hiding the problem by shrinking.

## Why This Works

`Plotly.react` has two internal paths. Without `layout.transition` it diffs and
performs a full supply-defaults + redraw, which creates, destroys, and repositions
DOM nodes. With a transition it hands off to the animation path, which walks the
*existing* node set and tweens numeric attributes, swapping text content on nodes
that are already there. Node creation has no "from" state to interpolate, so it
does not happen. Hence the precise signature: **values update, structure does not.**
Every symptom under Defect 1 is one instance of that rule.

`constraintext` defaults to `'both'`, meaning outside text is constrained to the
bar's extent — Plotly scales the text down rather than let it overflow its bar.
That is a reasonable default for dashboards and a bad one for a document where the
number is the point.

## Prevention

**1. Assert the rendered DOM against chart state — and assert legibility, not just
position.** `gd.layout` and `gd.data` were correct throughout both defects; any
check written against them passes. Only rendered-node assertions catch this class.

```js
function assertChartRender(id = 'cashflow-chart') {
  const gd = document.getElementById(id);
  const problems = [];

  // Structure: every annotation in state needs a node with matching text.
  const wanted = (gd.layout.annotations || []).map(a => a.text.replace(/<br>/g, ''));
  const rendered = [...gd.querySelectorAll('.annotation-text')].map(n => n.textContent);
  if (wanted.length !== rendered.length) {
    problems.push(`annotations: state ${wanted.length}, DOM ${rendered.length}`);
  }

  // Structure: every non-empty trace label needs a node.
  const wantedLabels = (gd.data[0].text || []).filter(Boolean).length;
  const nodes = [...gd.querySelectorAll('.barlayer text')].filter(t => t.textContent.trim());
  if (wantedLabels !== nodes.length) {
    problems.push(`labels: state ${wantedLabels}, DOM ${nodes.length}`);
  }

  // Legibility: nothing may be scaled below its declared size.
  nodes.forEach(t => {
    const m = /scale\(([\d.]+)\)/.exec(t.getAttribute('transform') || '');
    if (m && +m[1] < 0.95) problems.push(`label "${t.textContent}" scaled to ${(+m[1]).toFixed(2)}`);
  });

  if (problems.length) { console.error('CHART RENDER DRIFT', problems); return false; }
  return true;
}
```

Run after a scenario switch, after a live recompute with changed inputs, and after
a narrow → wide resize. There is no JS test runner in this repo (`tests/` is pytest
only), so this belongs in the manual `/qa` pass — **it is not covered by CI, and
should not be described as though it were.**

**2. Verify what rendered, not what you set.** Any diff-based renderer can accept
correct state and produce incorrect output. "The object holds the right value" is
not evidence the reader saw it. Start every wrong-number investigation at the DOM
node, not the framework's state object.

**3. Never pass a library's own object back into its diffing API when testing.**
Reference equality short-circuits the diff and guarantees a no-op regardless of
health.

**4. When a check passes, ask what it would have missed.** The overlap check was
correct and insufficient. A geometric assertion says nothing about size, contrast,
or clipping. Pair every "does it collide" with a "can it be read."

**5. Treat `layout.transition` as forbidden in this file.** Enforced by the comment
at the deletion site and by the `DECISIONS.md` Visualization entry.

## Related

- `FAILURES.md` → "2026-05-27 — Plotly resize listener accumulated on every form
  submit" — same file and library, unrelated root cause (a lifecycle guard stored
  on an object that gets replaced). Low overlap; neither entry would have prevented
  the other.
- `docs/plans/2026-05-26-001-…-plan.md:419` — "Always pass a new array reference
  for `y` … `Plotly.react` uses `===` identity to detect changes." The genuine
  near-neighbour: same family of "`react` silently skips updates when a subtle
  input condition isn't met," different trigger.
- `DECISIONS.md` → Visualization — the durable rules extracted from this.
- Provenance: `git log -S"transition:" -- static/app.js` returns exactly two
  commits — `3fafa25` introduced it undocumented, `fafff5e` removed it. Nothing in
  the knowledge store was contradicted because the transition was never written
  down. That is the failure mode, not an accident.

---

*Schema note: the `component` field is omitted deliberately. The ce-compound enum
is Rails-specific (`rails_view`, `frontend_stimulus`, `hotwire_turbo`, …) and this
project is FastAPI + vanilla JS with no Rails and no Stimulus. `frontend_stimulus`
was the closest value and would have been actively misleading in the repo's first
solution doc. Future docs here should omit it too, or the enum should gain a
`frontend_js` value upstream.*
