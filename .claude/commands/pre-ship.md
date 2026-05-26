---
description: Pre-ship checklist — verify the project works from scratch, secrets are excluded, and it's ready to share before shipping.
---

Run this before shipping, sharing, deploying, or calling something
"done." It catches the things that work on your machine but break
everywhere else.

Run this AFTER /ce:review and /qa, BEFORE shipping or /ce:compound.

Argument: $ARGUMENTS
- If $ARGUMENTS is provided, treat it as context for what kind of
  shipping (e.g., "deploying to production" vs "sharing with a friend"
  vs "submitting for class").
- If $ARGUMENTS is empty, run the full checklist.

## Step 1: Can it run from scratch?

### 1a. Dependencies declared
- Look for dependency files: package.json, requirements.txt,
  Pipfile, renv.lock, Gemfile, go.mod, Cargo.toml, etc.
- If none exist and the project uses external libraries, flag it.

### 1b. Lock file committed
- If there's a dependency file, check for a corresponding lock file.
- If the lock file exists but isn't tracked by git, flag it.

### 1c. Environment variables
- Check for .env files. If the project uses environment variables:
  - Is there a .env.example or .env.template?
  - Is .env in .gitignore?
  - Flag if .env exists but .env.example doesn't.

### 1d. README has setup instructions
- Does the README explain how to install deps, configure env vars,
  run the project, and run tests?

### 1e. Entry point works
- Try to identify and run the project's entry point.

## Step 2: Are secrets excluded?

### 2a. Hardcoded secrets
- Search for API keys, tokens, passwords hardcoded in source files.
- Variables named password, secret, token, api_key with hardcoded
  values (not env var references).

### 2b. Sensitive files
- Check if .env, credentials.json, private key files, or database
  files with real data are tracked by git.

### 2c. Gitignore coverage
- Is .gitignore present and reasonable for the project type?

## Step 3: Does it actually work end-to-end?

- Data project: does the data load? Do transformations run? Does
  output generate?
- Web app: does it start? Can you hit the main page? Do API endpoints
  respond?
- Script/tool: does it run with expected input? Handle missing input?

### 3a. Tests
- If tests exist: do they all pass? Run them and report results.
- If no tests exist: flag as a suggestion (not a blocker).

## Step 4: Is it pushed to a remote?

- Is a remote configured?
- Are all commits pushed?
- If not pushed, warn that work only exists on this machine.

## Step 5: Report

```
PRE-SHIP CHECKLIST — [date]

PASSED:
  [x] Dependencies declared and locked
  [x] No hardcoded secrets found
  [x] .gitignore covers sensitive files
  [x] Tests pass

FAILED:
  [ ] No .env.example (people won't know what vars to set)
  [ ] README missing setup instructions
  [ ] Not pushed to remote

VERDICT: [READY TO SHIP / FIX THESE FIRST]
```

If everything passed:
> "Looks ready to ship. Run /ce:compound to capture learnings,
> then you're done."

If there are failures:
> "Found [N] things to fix before shipping. Want to tackle them now?"

## Rules

- Don't block shipping over style issues.
- Secrets are always a blocker.
- Be specific about what's wrong and how to fix it.
- Always end with what command to run next.
