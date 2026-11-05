# Specialized AI Agent Roles

This directory defines specialized personas and system prompts for multi-agent workflows. Depending on the task complexity, an agent can adopt one of these roles or spawn subagents specialized for that domain.

## Available Roles

| Role | File | Primary Responsibility |
| :--- | :--- | :--- |
| **Architect Lead** | [`architect-lead.md`](./architect-lead.md) | High-level system design, schema modeling, API contract definition, ADR authoring |
| **Fullstack Developer** | [`fullstack-developer.md`](./fullstack-developer.md) | Feature implementation, component construction, bug fixes, refactoring |
| **QA & Test Engineer** | [`qa-test-engineer.md`](./qa-test-engineer.md) | Test suite creation, edge-case probing, regression testing, coverage analysis |
| **Security & Performance Auditor** | [`security-performance-auditor.md`](./security-performance-auditor.md) | Vulnerability analysis, secret leak prevention, profiling, latency optimization |
| **Documentation Curator** | [`documentation-curator.md`](./documentation-curator.md) | Memory synchronization, technical writing, diagram creation, API docs |

## How to Invoke / Activate
Agents can invoke these roles as subagents using Antigravity's `invoke_subagent` or `define_subagent` capabilities, or transition their working persona during a conversation turn.

