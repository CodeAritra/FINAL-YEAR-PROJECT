# Rule 01: Code Standards & Architecture Guidelines

All agents modifying code in this repository must adhere to the following principles:

## 1. Modularity & Clean Architecture
- Follow the Single Responsibility Principle: each module, function, or class should have one reason to change.
- Keep business logic decoupled from presentation layers and external APIs.
- Avoid large monolithic files. Prefer small, highly cohesive files (< 300 lines where practical).

## 2. Strong Typing & Strict Contracts
- If TypeScript: No `any` types unless strictly unavoidable and justified with a code comment. Always enable strict null checks.
- If Python: Use PEP 484 type hints across all function signatures and public class members. Run `mypy` or `pyright`.
- Define explicit interfaces/models for all external data inputs, API payloads, and database records.

## 3. Error Handling & Resilience
- Never write empty `catch` or `except` blocks. Log errors with contextual information (operation name, input arguments, stack trace).
- Handle edge cases explicitly: null/undefined checks, network timeouts, invalid inputs, division by zero, empty arrays/collections.
- Fail fast and provide human-readable, actionable error messages.

## 4. Documentation & Integrity
- Maintain existing comments and docstrings.
- Write clear docstrings for all non-trivial public functions, classes, and exported interfaces.
- Avoid obvious comments that merely restate code (e.g. `// increment i`). Comment on *why*, not *what*.

