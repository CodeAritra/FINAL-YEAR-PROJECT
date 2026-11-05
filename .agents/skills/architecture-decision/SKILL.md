---
name: architecture-decision
description: >-
  Standardized process for evaluating, drafting, and logging Architecture Decision Records (ADRs).
  Use this skill whenever choosing a framework, database, authentication provider, communication protocol, or major architectural design pattern.
---

# Architecture Decision Record (ADR) Skill

Use this workflow to make and document critical system decisions with clear rationale and trade-off analysis.

## Procedure

### 1. Identify the Architectural Question
Formulate the core question:
- What constraint, bottleneck, or feature requirement requires a decision?
- What are the non-negotiables (latency, cost, complexity, academic deadlines)?

### 2. Research & Compare Options
Formulate at least 2 viable options. Evaluate each on:
- Feasibility & development speed
- Maintainability & community support
- Performance & resource consumption
- Alignment with project requirements

### 3. Log in `memory/decisions.md`
Append the new ADR using the standardized template:
```markdown
### ADR-XXX: [Descriptive Title]
- **Date**: YYYY-MM-DD
- **Status**: Accepted
- **Deciders**: User, Architect Agent
- **Context & Problem Statement**: [Why this decision is needed]
- **Considered Options**:
  1. [Option 1] - [Pros/Cons]
  2. [Option 2] - [Pros/Cons]
- **Decision Outcome**: [Chosen option and justification]
- **Consequences**:
  - Positive: [Benefits]
  - Negative: [Trade-offs or additional complexity]
```

### 4. Communicate & Align
Summarize the decision and trade-offs directly to the user for final sign-off before broad implementation.

