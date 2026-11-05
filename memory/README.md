# Persistent Memory System

This directory acts as the external brain and persistent state for AI agents working in this repository. It preserves context across conversations, IDE restarts, model transitions, and long breaks in development.

## Directory Structure

- **`context.md`**: Core project identity, problem domain, goals, system architecture, tech stack, and prerequisites.
- **`decisions.md`**: Architecture Decision Records (ADRs) tracking significant technical choices, rationale, and discarded alternatives.
- **`tasks.md`**: Active development roadmap, sprint backlog, task breakdowns, priorities, and completion status.
- **`progress.md`**: Chronological log of sessions, milestones, features completed, and known blockers.
- **`learnings.md`**: Technical insights, quirks of external APIs/libraries, unexpected edge cases, and debugging retrospectives.

## Guidelines for AI Agents

1. **Always Read on Wakeup**:
   Every agent begins by inspecting `context.md` and `tasks.md`.
2. **Never Overwrite Without Preserving History**:
   Append new entries chronologically in `progress.md`, `decisions.md`, and `learnings.md`.
3. **Keep State Clean and Actionable**:
   Clean up completed items in `tasks.md` by moving them to the "Completed" section with references to commits or PRs.
4. **Human Review Friendly**:
   Format every file in clean Markdown so the project owner can read, audit, or edit the files directly at any time.

