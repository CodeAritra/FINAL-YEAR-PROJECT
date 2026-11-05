# Project Learnings & Knowledge Base

This file captures tricky bugs solved, quirks of third-party libraries, performance traps, edge-case behaviors, and valuable technical discoveries made while developing this project.

---

## Knowledge Index

| Category | Title | Date Added | Summary |
| :--- | :--- | :--- | :--- |
| Workspace | Antigravity File System & Hierarchical Rules | 2026-11-05 | Rules in `.agents/rules/` and `AGENTS.md` automatically load; skills follow progressive disclosure. |

---

## Logged Learnings

### LRN-001: Antigravity Customization Discovery & Directory Hierarchy
- **Context**: Setting up repository customizations on Windows.
- **Problem / Discovery**: Antigravity automatically discovers customizations under `.agents/` at repository root, in addition to hierarchical root `AGENTS.md`. Skills require a strict frontmatter format (`name` and `description`) to be discoverable and load via progressive disclosure.
- **Solution / Takeaway**: All skills must include lowercase hyphenated names and actionable descriptions stating *what* and *when* to activate. High-volume reference materials should be separated into `references/` directories within each skill.

