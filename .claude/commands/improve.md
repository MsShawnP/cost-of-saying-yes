---
description: Review and improve an existing project. Audits code, workflow files, and structure, then guides you through fixing what matters.
---

Run a guided improvement pass on this project. Works on any project
that already has code or files — this is for making existing things
better, not starting from scratch.

Argument: $ARGUMENTS

**Modes:**
- `/improve` — full workflow: audit + plan + fix + track
- `/improve audit-only` — audit and report only, no fixes. Good for
  regular health checks or deciding which project needs attention.
- `/improve [topic]` — focus the improvement on a specific area
  (e.g., `/improve tests` or `/improve the data pipeline is flaky`)

If $ARGUMENTS contains "audit-only" or "audit only", run in
audit-only mode: Steps 1-4 only, then log the audit in Step 7
and stop. Do not create an improvement arc or execute fixes.

If $ARGUMENTS contains anything else, treat it as context for what
the user wants to focus on.

If $ARGUMENTS is empty, run the full check-in + audit + improve flow.

## Step 1: Check for workflow files

Look for these files in the project root:
- CLAUDE.md, PLAN.md, HANDOFF.md, DECISIONS.md, FAILURES.md

If none exist, tell the user:
> "This project doesn't have workflow files yet. I can add them first
> so we can track what we improve. Want me to run /add-workflow to
> set that up, then come back to the improvement pass?"

If the user says yes, run /add-workflow first, then return to Step 2.
If the user says no, continue without workflow files — you can still
audit and improve, you just won't have PLAN.md to write the
improvement arc into.

## Step 2: Quick check-in

Ask these three questions. Ask them one at a time — wait for each
answer before asking the next.

1. "What's bugging you about this project right now? Anything you've
   been putting off or that doesn't feel right?"

2. "Is there a part of the code you're least confident about — like
   something that works but you're not sure why, or something you'd
   be nervous to change?"

3. "Anything you want me to NOT touch? (Files, features, or areas
   that should stay as-is.)"

If $ARGUMENTS was provided, you can fold it into the first question:
"You mentioned [argument]. Tell me more about that — and is there
anything else bugging you?"

Keep their answers. You'll merge them with audit findings in Step 4.

## Step 3: Audit the project

Read through the project and assess each category below. For each
item, note whether it's fine, needs attention, or is missing entirely.

Be thorough but don't manufacture problems. If something works and
is clear, say so.

### 3a. Workflow files (skip if project has none)

- **CLAUDE.md:** Is the project description filled in? Stack section?
  Voice section? Or is it still the template with brackets?
- **PLAN.md:** Is there an active arc? Are tasks specific and
  actionable? Any stale checked/unchecked items from weeks ago?
- **HANDOFF.md:** When was the last entry? Is there uncommitted work
  that happened since then?
- **DECISIONS.md:** Any decisions logged? Anything in the code that
  clearly represents a choice but isn't documented here?
- **FAILURES.md:** Any entries? Is the project old enough that the
  absence of failure entries suggests they're not being captured?

### 3b. Code quality

- **File organization:** Are files in sensible locations? Any loose
  scripts in the root that should be in src/ or similar?
- **Naming:** Are files, functions, and variables named clearly enough
  that you can tell what they do without reading the body?
- **Dead code:** Anything commented out or obviously unused?
- **Duplication:** Any copy-paste patterns that should be a shared
  function?
- **Error handling:** Are errors handled at system boundaries (user
  input, file I/O, API calls)? Ignore internal code — only check
  boundaries.

### 3c. Tests

- Do tests exist? If yes, do they run and pass?
- Are the most important code paths tested?
- If no tests exist, identify the 2-3 things that should be tested
  first. Not everything — just the highest-value targets.

### 3d. Dependencies

- Are dependencies declared (package.json, requirements.txt,
  renv.lock, Gemfile, etc.)?
- Anything obviously outdated or pinned to a version with known
  issues?

### 3e. Documentation

- Is there a README? Does it explain what the project is and how to
  run it?
- Could someone else (or you in 3 months) pick this up and get it
  running without asking you questions?

### 3f. Git hygiene

- Any uncommitted changes sitting around?
- Any large files tracked in git that shouldn't be (data files,
  binaries, node_modules)?
- Is .gitignore reasonable for the project type?

### 3g. Deep reviews (automated)

After the manual audit above, run these automated reviews to catch
things a read-through might miss.

1. **Security review:** Run /security-review on the project.
2. **Code quality review:** Run /ce:review on the project.
3. **Data and analysis review (if applicable):** If the project does
   any math, calculations, data transformations, statistical analysis,
   aggregations, or metric definitions, run the data-science-reviewer
   agent. Skip if the project has no data, math, or analysis components.

If any skill is not available, skip it and note in the findings.

## Step 4: Present findings

Organize everything into three priority levels:

### CRITICAL — should fix (blocks progress or has real problems)
### IMPORTANT — worth improving (quality and maintainability)
### NICE TO HAVE — polish (organization and style)

For each finding: one sentence what's wrong, one sentence what fixing
it looks like.

After presenting, check the mode:

**If audit-only mode:** Skip to Step 7. Ask:
> "That's the audit. No fixes today — this is just the health check.
> Anything here surprise you or that you want to flag for next time?"

**If full improve mode:** Ask:
> "Which of these do you want to tackle?"

## Step 5: Create improvement arc in PLAN.md

Based on what the user chose, create a new arc in PLAN.md.

## Step 6: Execute improvements

Work through the plan items one at a time. Show the user what you're
changing and why before making each change. Verify it works. Confirm
before moving to the next item.

After all improvements are complete, if the project has any UI or
browser-visible output, suggest running /qa.

## Step 7: Log the audit/improvement

Add an entry to the **Improvement History** section at the bottom of
PLAN.md:

For **audit-only** mode:
```
### [YYYY-MM-DD] — Audit (health check only)
- **Findings:** [count] critical, [count] important, [count] nice-to-have
- **Top concerns:** [1-3 sentence summary]
- **Action taken:** Audit only — no fixes this session
- **Next review:** [date]
```

For **full improve** mode:
```
### [YYYY-MM-DD] — Improvement pass
- **Trigger:** [user-initiated / scheduled review]
- **What was reviewed:** [areas covered]
- **What was fixed:** [list of changes made]
- **Deferred:** [anything identified but not fixed]
- **Next review:** [date]
```

### Audit frequency guide

| Project state | Audit every |
|---|---|
| Active (commits in last 2 weeks) | 2-4 weeks |
| Stable (no commits in 30+ days) | 90 days |
| Just shipped | Right after shipping |
| Inherited/new-to-you | Immediately |

Then suggest running /wrap.

## Rules

- Do not change code without showing the user what you're changing and why.
- Do not refactor working code just because it could be "cleaner"
  unless the user specifically asked for it.
- If the project has no tests, pick the 2-3 most critical things to
  test first — not everything.
- Be honest about what you find. Don't manufacture problems or
  downplay real issues.
- Explain findings in plain language.
- Do not push to remote. Local changes only.
