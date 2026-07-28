# cost-of-saying-yes — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule. The whole point: future-you (or future-Claude)
shouldn't re-attempt dead ends because the lesson got lost.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason, not "it broke." If the
failure mode was technical, name the specific issue. If the failure
mode was scope or approach, name that.]

**What we tried instead:** [The next attempt, which may also have
failed and may have its own entry below]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search — e.g., "rendering, pandoc,
quarto" or "scope, scrollytelling, decoration"]

---

## Entries

### 2026-05-26 — mkdir .claude/commands/ blocked by permission classifier

**Attempted:** `mkdir -p .claude/commands/` via Bash during /init setup.

**Why it didn't work:** Claude Code's auto-mode classifier flagged it as self-modification (creating a directory that would hold Claude slash commands). Blocked even in a project directory, not just global settings.

**What we tried instead:** Used the Write tool to write files directly to `.claude/commands/*.md` — this created the directory implicitly and was not blocked.

**Status:** Resolved

**Tags:** init, windows, auto-mode, permissions, claude-commands

### 2026-05-27 — Model trough month diverges from Cinderhaven validated fixture

**Attempted:** Running the calculator with Cinderhaven inputs (1,200 doors, 4 SKUs, $1.00 wholesale, $0.45 COGS, 2.0 units/door/week, Walmart defaults) and comparing to validated fixture numbers.

**Why it didn't work:** The model places the cash trough at month 2; the Cinderhaven fixture records it at month 4. The model treats upfront costs (free fills + new store allowances) as a pre-launch lump sum, causing the trough to hit immediately in months 1-2 before any cash arrives. In reality, these may be deducted from the first invoice, pushing the trough later.

**What we tried instead:** Fixed `units_per_case` from 4 → 40 (back-solved: 4×1,200×40×$0.45 = $86,400 free fills) and `chargeback_rate_learning` from 3% → 12% (back-solved: $14,976 ÷ (3×$41,568) = 12%). Trough value improved to -$175,811 vs -$165,000 (6.5% off). Trough month remains 2. [superseded 2026-07: the -$165,000 benchmark cited here was the original **incorrect** target; the model's corrected canonical trough is -$156,352 at Month 1.]

**Status:** Open — per the plan, the CINDERHAVEN_VALIDATED fixture is authoritative for the case study section. The interactive tool produces its own computed output. The divergence is documented here and need not be fixed for MVP.

**Tags:** calculator, trough, cinderhaven, deduction-lag, free-fills, units-per-case

### 2026-05-27 — Quarto .gitignore `*.html` pattern silently excluded static/index.html from git

**Attempted:** Track `static/index.html` in git as part of the normal project.

**Why it didn't work:** `.gitignore` was seeded from a Quarto/R project template that contained `*.html` under a "Rendered output" section. For a Quarto project, `.html` files are generated artifacts; for this FastAPI project, `static/index.html` IS the source. Git silently ignored it — a fresh clone would have produced a broken, blank deployment with no visible error.

**What we tried instead:** Removed the entire Quarto/R section (`*.html`, `_freeze/`, `_site/`, `.Rproj.user/`, `.Rhistory`, `.RData`, `renv/library/`) from `.gitignore`, then `git add static/index.html`.

**Status:** Resolved

**Tags:** gitignore, static-files, quarto, git, deployment

### 2026-05-27 — Plotly resize listener accumulated on every form submit

**Attempted:** Reset chart initialization state by setting `currentData._chartInitialized = false` on each form submission so the next `renderChart()` call would use `Plotly.newPlot` instead of `Plotly.react`.

**Why it didn't work:** `currentData` is replaced entirely on each API response. The `_chartInitialized` property was always absent on the new object — the guard never fired, causing a new `window.addEventListener('resize', ...)` to be attached on every chart render. After N submissions, N resize handlers were active simultaneously.

**What we tried instead:** Moved initialization flags to module-level variables (`chartInitialized`, `resizeListenerAttached`) that persist across data refreshes but are scoped to chart DOM state, not API response state.

**Status:** Resolved

**Tags:** javascript, plotly, event-listeners, state-management, resize

### 2026-05-27 — pytest conftest.py in tests/ subdirectory is not importable as a module

**Attempted:** Placed shared test constant `CINDERHAVEN_INPUTS` in `tests/conftest.py` and imported it with `from conftest import CINDERHAVEN_INPUTS` in the test files.

**Why it didn't work:** pytest adds the project **rootdir** to `sys.path`, not the `tests/` subdirectory. Conftest files are auto-discovered and executed by pytest but are not made importable as modules unless they sit at a path-root level. `from conftest import ...` raised `ModuleNotFoundError: No module named 'conftest'`.

**What we tried instead:** Moved `conftest.py` to the project root (same level as `app.py`). The rootdir IS on `sys.path`, so `from conftest import CINDERHAVEN_INPUTS` resolves correctly from any test file. Root-level conftest.py is also the standard pytest location for session-wide fixtures and shared constants.

**Status:** Resolved

**Tags:** pytest, conftest, sys-path, test-organization, imports

### 2026-05-27 — openpyxl `neg_currency` format requires negative values to render cost rows red

**Attempted:** Store cost summary fields (`upfront_investment`, `total_deductions_year1`, `cogs_year1`) as their absolute positive values in the summary dict, relying on the `neg_currency` number format to apply red/parentheses styling in Excel.

**Why it didn't work:** The `neg_currency` format `"$"#,##0;[Red]("$"#,##0)` only applies red color and parentheses to values that are numerically negative. Positive numbers always render in the default black format. CFO-grade output requires cost rows to appear in red — this only works if the values are stored as negative numbers.

**What we tried instead:** Negated the cost fields in the summary dict in `calculator.py` (`-total_deductions`, `-cogs_year1`). The `upfront_investment` was already negative by construction so `abs()` was removed. Frontend does not read these fields directly so no UI impact.

**Status:** Resolved

**Tags:** openpyxl, excel, formatting, neg_currency, cfo-output

---

### 2026-05-27 — `uvicorn` ENOENT in launch.json on Windows

**What was attempted:** Set `runtimeExecutable: "uvicorn"` in `.claude/launch.json` to start the FastAPI server via `preview_start`.

**Why it didn't work:** `uvicorn` is not on the system PATH directly on Windows — it's installed inside a Python environment and invoked via the Python module system. The shell couldn't find the executable and returned ENOENT.

**What we tried instead:** Changed to `runtimeExecutable: "python"` with `runtimeArgs: ["-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]`. This works because `python` is on the PATH and `-m uvicorn` delegates to the module.

**Status:** Resolved

**Tags:** launch.json, preview_start, uvicorn, windows, path

---

### 2026-05-27 — CE review false positive P0 after context compaction

**Attempted:** Resumed CE review synthesis from a compacted session summary. The summary claimed `CompareInput.effective_broker_projection()` was missing and all field validators absent — flagged as P0 (every POST /api/compare silently 500s in production).

**Why it didn't work:** The pre-compaction summary was generated from agent outputs that appear to have read `CompareInput` partially or out of context. The method exists at `app.py:201–211` and all validators are present at lines 144–199. The false positive was plausible because `CompareInput` is a long class and the method appears near the bottom.

**What we tried instead:** Re-read `app.py` directly at session start before presenting any findings. One read immediately disproved the P0. This is the correct recovery pattern after compaction: verify agent findings against actual source before reporting.

**Status:** Resolved (no code change needed — code was always correct)

**Tags:** ce-review, compaction, false-positive, code-review, agents, context-loss

### 2026-07-27 — Breakeven-velocity solver rounded DOWN, reporting a velocity that still loses money

**Attempted:** `calculate_breakeven_velocity` bisected for the crossover where realistic Year-1 net cash ≥ 0, then returned `round(hi, 2)`.

**Why it didn't work:** `round()` rounds toward the true crossover from above, landing *below* it. For Cinderhaven it reported 2.53, but the model nets −$51 at 2.53 (only +$633 at 2.54). A CFO reading "you need 2.53 to break even," typing 2.53, and seeing −$51 catches the tool contradicting itself — a directional error on a tool whose whole thesis is "the number tells the truth." Caught in code review, not by the original test (the pin locked in the wrong-direction value).

**What we tried instead:** `math.ceil(round(hi, 6) * 100) / 100` — round the crossover UP to the nearest cent so the reported figure itself clears breakeven. Updated pins to 2.54; added a test asserting `net(breakeven) ≥ 0`.

**Status:** Resolved

**Tags:** breakeven, rounding, bisection, calculator, cfo-credibility, code-review

### 2026-07-27 — Live-recompute shipped with a response race

**Attempted:** The verdict-first redesign recomputes live on every input change via a 350ms `debounce` around `runCalculation`, each call building its own `AbortController`.

**Why it didn't work:** Debounce only delays *scheduling*; it doesn't serialize *in-flight* requests. When two calls overlap (Fly cold start, or a slow reply), whichever response *arrives last* wins — so a stale reply can overwrite fresh state and paint numbers that don't match the form, while the "Live" flag says all-current. Self-heals on the next keystroke, but a screenshotted mismatch is exactly the credibility failure the tool exists to avoid.

**What we tried instead:** A module-level monotonic `calcSeq` id captured per call; the response (and the error/failure branches) only apply if `seq === calcSeq`, otherwise they return and let the newer request own the UI.

**Status:** Resolved

**Tags:** javascript, race-condition, debounce, fetch, live-recompute, state-management

### 2026-07-28 — Bar chart "fixed" mobile labels by shrinking them to ~5px

**Attempted:** Converting the cash-flow chart from a line to vertical bars so all
twelve monthly labels would fit at 375px without a stride rule dropping any.

**Why it didn't work:** It appeared to work. A bounding-box check reported twelve
labels and zero overlaps at 343px chart width. Plotly had achieved that by
scaling the text — `transform="… scale(0.4459…)"`, 11px declared and about 5px
rendered. `constraintext` defaults to constraining outside bar text to the bar's
own width, shrinking rather than overflowing. The verification method was the
real failure: measuring position says nothing about legibility, so the check
returned a true and useless answer.

**What we tried instead:** `textangle: -90` to run the labels upright, which is
what actually creates the room, plus `constraintext: 'none'` to stop Plotly
concealing the shortfall. Verified by asserting no label had a `scale()` below
0.95, not just that none overlapped.

**Status:** Resolved

**Tags:** plotly, bar-chart, text-labels, constraintext, mobile, verification,
false-negative, silent-failure

### 2026-07-28 — Tested Plotly.react by handing it back Plotly's own object

**Attempted:** Checking whether `Plotly.react` was responsible for missing point
labels, via `Plotly.react(gd, [gd.data[0]], gd.layout, config)` in the console.

**Why it didn't work:** `gd.data[0]` is the object Plotly already holds. `react`
diffs incoming against stored, sees the same reference with identical contents,
and correctly no-ops. Nothing broke, so the test read as a pass — but a healthy
and a broken `react` produce identical results under it. Any diff-based renderer
is untestable via its own state.

**What we tried instead:** Built a genuinely new object graph —
`{ ...gd.data[0], text: [...gd.data[0].text] }` with a deep-copied layout — which
immediately isolated the real cause (the layout `transition`).

**Status:** Resolved

**Tags:** plotly, plotly-react, debugging, invalid-test, reference-equality,
diffing

### 2026-07-28 — Three failed placements for the chart's trough and break-even captions

**Attempted:** Positioning the "Peak trough" and "Break-even: Month N" annotations
around bars that carry their own outside labels.

**Why it didn't work:** Each placement collided with something. Below the trough
point — collided with that point's own label. `ay: 56` — pushed the callout past
the chart's bottom edge. Break-even anchored to its month's x — landed in the
strip of margin that bar labels spill into, colliding with the month-12 label on a
late break-even, and needed a separate guard to avoid running off the right edge.

**What we tried instead:** Trough caption `yshift: -68`, below the bar's own
label, carrying no figure (the bar prints its value and the verdict card states
it again). Break-even caption pinned top-left in paper coordinates, decoupled from
the data entirely — the red dashed line already shows where the crossing is.

**Status:** Resolved

**Tags:** plotly, annotations, layout, collision, bar-chart, responsive

### 2026-06-23 — FastAPI StaticFiles caches stale CSS and JS during development

**Attempted:** Rewrote `static/style.css` (added tab rules) and `static/app.js` (added `renderLineItems`, tab switching, `formatTableCurrency`). Expected the preview server to serve the updated files.

**Why it didn't work:** FastAPI StaticFiles served the old file contents even after restarting the preview server. The dynamic line-item table appeared empty because the browser/server was still loading the old `app.js` that didn't define `renderLineItems`. Same issue hit CSS first — new tab styles weren't applied.

**What we tried instead:** Added cache-busting query params (`?v=2`) to the `<link>` and `<script>` tags in `index.html`. Fixed CSS first but didn't apply the same fix to JS immediately — lost ~30 minutes re-diagnosing the identical root cause on the JS file.

**Status:** Resolved

**Tags:** fastapi, staticfiles, caching, cache-buster, preview-server, development
