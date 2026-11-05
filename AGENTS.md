# Agent Operational System & Repository Protocol

Welcome to the project workspace. This file defines the core operating procedures, multi-agent collaboration patterns, quality gates, and the persistent memory protocol for all AI agents working in this repository.

---

## 1. Operating Principles

1. **Memory-First Execution**:
   - At the beginning of every session or task, read `memory/context.md` and `memory/tasks.md` to restore full context before proposing or implementing changes.
   - Do not ask the user for context that is already recorded in the `memory/` directory.

2. **Verify Before Declaring Success**:
   - Never assume code works. Execute automated tests, run linters, or perform local probes.
   - If tests do not exist, write them before marking a task complete.

3. **Incremental & Non-Destructive**:
   - Make atomic, reviewable changes.
   - Preserve existing unrelated code, comments, configurations, and documentation.
   - Never delete or refactor working code without clear justification recorded in `memory/decisions.md`.

4. **Continuous Memory Synchronization**:
   - Automatically record key architecture decisions, progress milestones, task completions, and debugging learnings into the `memory/` files during and at the conclusion of tasks.

---

## 2. Persistent Memory Protocol

All persistent project state is maintained in the `memory/` directory. All agents must read from and write to these structured files:

| File | Purpose | When to Read | When to Update |
| :--- | :--- | :--- | :--- |
| `memory/context.md` | Core mission, architecture, tech stack, env setup | Start of every session | When project scope, stack, or architecture changes |
| `memory/tasks.md` | Active roadmap, current sprint, backlog, completed items | Start of every session & before starting tasks | As tasks transition (Pending → In Progress → Done) |
| `memory/progress.md` | Chronological session logs, milestones, deliverable history | When understanding recent project evolution | At the end of every significant task or session |
| `memory/decisions.md` | Architecture Decision Records (ADRs) and trade-offs | When designing features or choosing libraries | Whenever an architectural or design choice is made |
| `memory/learnings.md` | Gotchas, edge cases, bug root causes, environment quirks | When debugging or troubleshooting errors | Whenever a tricky bug or non-obvious solution is discovered |

### Memory Update Standard
- Keep entries timestamped (`YYYY-MM-DD`).
- Keep entries structured, concise, and actionable.
- Link relevant code paths using markdown file links (`[file](path/to/file)`).

---

## 3. Specialized Agent Roles

When tackling complex problems, activate or embody the appropriate specialized persona:

1. **System Architect (`.agents/roles/architect-lead.md`)**:
   - Responsible for system design, database schemas, API contracts, tech stack evaluation, and ADR creation.
2. **Fullstack Developer (`.agents/roles/fullstack-developer.md`)**:
   - Responsible for robust, type-safe, modular code implementation, feature delivery, and bug fixes.
3. **QA & Test Engineer (`.agents/roles/qa-test-engineer.md`)**:
   - Responsible for unit, integration, and E2E testing, boundary testing, test fixtures, and edge cases.
4. **Security & Performance Auditor (`.agents/roles/security-performance-auditor.md`)**:
   - Responsible for vulnerability scanning, input validation, authentication/authorization checks, latency, and profiling.
5. **Documentation & Memory Curator (`.agents/roles/documentation-curator.md`)**:
   - Responsible for synchronizing `memory/`, generating diagrams, keeping API documentation and README files accurate.

---

## 4. Reusable Skills Catalog

The repository includes specialized workspace skills under `.agents/skills/`:

- **`memory-sync`**: Protocol and scripts to read, update, and maintain persistent state.
- **`project-onboarding`**: Step-by-step ingestion workflow when user provides project requirements or codebase transfers.
- **`verification-gate`**: Standardized pre-merge validation (typecheck, lint, test, security review).
- **`architecture-decision`**: Template and workflow for drafting Architecture Decision Records (ADRs).

---

## 5. Project Quality & Governance Rules

All agent interactions must adhere to the modular rules defined in `.agents/rules/`:

1. `01-code-standards.md`: Modularity, clean code, DRY, SOLID, strict typing, structured logging, defensive coding.
2. `02-git-workflow.md`: Conventional commit formatting (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`), branch conventions.
3. `03-testing-verification.md`: Mandatory test execution, reproduction before bug fixing, regression prevention.
4. `04-security-safety.md`: Zero hardcoded secrets, environment variable isolation (`.env`), input sanitization, safe command execution.

---

## 6. Standard Session Workflow

```
┌────────────────────────────────────────────────────────┐
│ 1. SESSION INITIALIZATION                               │
│    - Read memory/context.md and memory/tasks.md         │
│    - Identify current objective and active state        │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 2. PLANNING & ROLE SELECTION                            │
│    - Select appropriate role (Architect / Dev / QA)    │
│    - Consult relevant skills and rules                  │
│    - Formulate verifiable implementation plan          │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 3. EXECUTION & VERIFICATION                             │
│    - Implement changes incrementally                    │
│    - Run tests and linters via sandbox                  │
│    - Fix any regressions immediately                    │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 4. MEMORY SYNCHRONIZATION                               │
│    - Record ADRs in memory/decisions.md (if any)        │
│    - Document discoveries in memory/learnings.md        │
│    - Update memory/tasks.md status                      │
│    - Append session summary to memory/progress.md       │
└────────────────────────────────────────────────────────┘
```

