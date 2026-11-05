# Rule 03: Testing & Verification Protocol

Assumptions are bugs waiting to happen. Every agent must rigorously verify their work.

## 1. Mandatory Verification
- Never declare a coding task complete without executing automated tests, linters, or a sandbox execution run.
- When fixing a bug:
  1. First reproduce the bug with a failing test case or direct command reproduction.
  2. Implement the fix.
  3. Verify that the test passes and no regressions were introduced.

## 2. Test Structure
- Unit Tests: Test business logic in isolation with mock dependencies.
- Integration Tests: Test cross-module behavior, database queries, and API endpoints.
- Smoke Tests: Verify that the server or application boots up cleanly without runtime errors.

## 3. Test Coverage Expectations
- Aim for high test coverage on core business logic, algorithmic modules, and security-critical functions.
- Every new feature must be accompanied by corresponding test suites.

