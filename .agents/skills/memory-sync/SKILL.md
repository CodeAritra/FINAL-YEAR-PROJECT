---
name: memory-sync
description: >-
  Synchronizes persistent state in the memory/ directory across session boundaries.
  Use this skill at the beginning of a session to load context, during a session when decisions or learnings occur, and at the end of a session to record progress and task status.
---

# Memory Synchronization Skill

Use this workflow to ensure persistent project state is never lost between sessions or conversational turns.

## Procedure

### 1. Session Wakeup (Input Sync)
1. Read `memory/context.md` to identify the project domain, tech stack, and goals.
2. Read `memory/tasks.md` to identify current sprint tasks, priorities, and blockers.
3. Check `memory/learnings.md` if handling a task related to a previously recorded issue.

### 2. In-Flight Capture
- **Architectural or Design Choices**:
  - Immediately append an entry to `memory/decisions.md` following the ADR format (Context, Options, Decision, Consequences).
- **Novel Bug / Technical Insight**:
  - Immediately append an entry to `memory/learnings.md` detailing the problem, root cause, and concrete fix.

### 3. Session Wrap-up (Output Sync)
1. Update `memory/tasks.md`:
   - Move completed tasks from Current Sprint to Completed Tasks with timestamp.
   - Adjust statuses of in-progress or blocked tasks.
2. Update `memory/progress.md`:
   - Append a new Session entry with Date, Goal, Completed items, Decisions logged, and Next steps.

