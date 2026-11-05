---
name: project-onboarding
description: >-
  Ingests new project context, problem statements, requirements, and tech stack details provided by the user.
  Use this skill when the user provides initial project information, specifications, course guidelines, or codebase handoffs.
---

# Project Onboarding Skill

Use this workflow immediately when the user shares their project description, requirements, or final year project brief.

## Procedure

### Step 1: Analyze & Parse User Context
Carefully parse the user's input and extract:
1. **Core Problem Statement**: What does this system solve?
2. **Primary Deliverables & Scope**: What are the must-haves, nice-to-haves, and out-of-scope elements?
3. **Target Technology Stack**: Preferred or mandated languages, frameworks, databases, and external APIs.
4. **Academic / Final Year Specifics**: Evaluation criteria, demo requirements, documentation/report needs, presentation deliverables.

### Step 2: Update Persistent Context (`memory/context.md`)
1. Edit `memory/context.md` with:
   - Specific project title and summary
   - Detailed functional objectives
   - Confirmed tech stack and dependencies
   - Mermaid diagram representing the high-level system architecture
   - Local prerequisites and execution commands

### Step 3: Populate Roadmap & Tasks (`memory/tasks.md`)
1. Break down the project into logical milestones (e.g., Milestone 1: MVP / Core Engine, Milestone 2: UI & Integration, Milestone 3: Testing & Polish).
2. Populate the High-Priority sprint with immediate actionable tasks.

### Step 4: Record Initial Architecture Decision (`memory/decisions.md`)
1. Log `ADR-002: Core Technology Stack & Architecture Selection` capturing why the chosen stack was selected.

### Step 5: Log Progress & Confirm with User
1. Update `memory/progress.md`.
2. Present a concise structured summary back to the user, highlighting:
   - Synthesized project understanding
   - Proposed milestone roadmap
   - Immediate next action ready for execution

