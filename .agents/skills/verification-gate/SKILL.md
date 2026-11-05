---
name: verification-gate
description: >-
  Validates code changes through linting, typechecking, running automated test suites, and performing smoke tests.
  Use this skill before declaring a task complete, after refactoring code, or before preparing a release or milestone delivery.
---

# Verification Gate Skill

Use this workflow to ensure zero regressions and high code quality before finishing any technical task.

## Procedure

### 1. Static Analysis & Type Checking
- For TypeScript/Node:
  ```bash
  npm run typecheck # or tsc --noEmit
  npm run lint
  ```
- For Python:
  ```bash
  mypy .
  flake8 . # or ruff check .
  ```

### 2. Automated Test Execution
- Run unit and integration tests:
  ```bash
  npm test # or pytest
  ```
- Verify test output:
  - 100% tests passing.
  - Zero unhandled rejections or uncaught exceptions.

### 3. Sanity & Smoke Check
- Start the application in test mode or dry-run mode to confirm clean bootstrap without crashes.
- Verify environment variable presence and error messaging on missing required keys.

### 4. Logging & Task Sign-off
- If all checks pass: update `memory/tasks.md` marking the task as completed.
- If checks fail: address errors immediately, re-run verification, and log any non-trivial discovery in `memory/learnings.md`.

