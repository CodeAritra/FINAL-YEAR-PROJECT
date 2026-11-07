# Architecture Decision Records (ADRs)

This document tracks all significant architectural, architectural pattern, library, and system design decisions made during the project.

---

## ADR Template

```markdown
### ADR-XXX: [Short Title of the Decision]
- **Date**: YYYY-MM-DD
- **Status**: [Proposed | Accepted | Superseded | Deprecated]
- **Deciders**: [e.g., User, Architect Agent]
- **Context & Problem Statement**: What problem are we solving? What are the constraints?
- **Considered Options**:
  1. Option A (Pros / Cons)
  2. Option B (Pros / Cons)
- **Decision Outcome**: Chosen option and key justification.
- **Consequences**:
  - Positive consequences (benefits gained)
  - Negative consequences / trade-offs accepted
```

---

## Logged Decisions

### ADR-001: Persistent Multi-Agent Workspace Architecture
- **Date**: 2026-11-05
- **Status**: Accepted
- **Deciders**: User, AI Assistant
- **Context & Problem Statement**: The project needs a robust mechanism to retain knowledge, decisions, task progress, and learnings across AI pair-programming sessions without context window loss.
- **Considered Options**:
  1. Rely solely on conversation history and chat transcripts (Lossy, transient, not persisted in VCS).
  2. File-based persistent memory system (`memory/`) combined with declarative agent instructions (`AGENTS.md`) and `.agents/` customizations.
- **Decision Outcome**: Option 2. We establish a clean Markdown-based memory directory (`context.md`, `decisions.md`, `tasks.md`, `progress.md`, `learnings.md`) integrated with Antigravity hierarchical discovery and role definitions.
- **Consequences**:
  - Positive: Instant state restoration, clear human auditability, git-trackable progress, zero dependency on external vector DBs or proprietary memory clouds.
  - Negative: Requires agents to diligently update files during sessions.



### ADR-002: Hybrid Architecture for Memory-Constrained Research Pipeline
- **Date**: 2026-11-05
- **Status**: Accepted
- **Deciders**: User, Architect Agent
- **Context & Problem Statement**: The project must run research-grade RAG evaluation on an 8 GB RAM laptop. Running multiple large models locally (LLM + Llama Guard + DeBERTa + Presidio) causes Out-Of-Memory (OOM) errors and severe system thrashing.
- **Considered Options**:
  1. Full local deployment using quantized models (Ollama local + local PyTorch models). Requires >16 GB RAM for simultaneous evaluation.
  2. Pure cloud SaaS APIs (OpenAI / Anthropic only). Exposes private credentials and lacks granular inspection into model weights/layers.
  3. Hybrid Architecture: Local lightweight tasks (Typer CLI, PyMuPDF, Presidio PII, Regex secret detector, lightweight `all-MiniLM-L6-v2` embeddings) + Cloud/Hosted services for heavy tasks (Qdrant Cloud vector DB, hosted Ollama/Qwen2.5, hosted Hugging Face endpoints for Llama Guard and DeBERTa).
- **Decision Outcome**: Option 3 (Hybrid Architecture).
- **Consequences**:
  - Positive: Guarantees smooth execution under 8 GB RAM without sacrificing research rigor or accuracy.
  - Negative: Requires network access and API credentials stored safely in `.env`.


### ADR-003: Dual Model Execution Modes (Hosted vs. Local Ollama) & Architecture Realignment
- **Date**: 2026-11-05
- **Status**: Accepted
- **Deciders**: User, Architect Agent
- **Context & Problem Statement**: The framework required strict delineation of model responsibilities, support for both cloud-hosted (Groq) and local LLM (Ollama) inference, removal of obsolete models (Sentence Transformers and Llama Guard 3), and integration of Gemini Embedding 2 and Llama Prompt Guard 2 86M.
- **Considered Options**:
  1. Monolithic provider bindings inside RAG modes.
  2. Decoupled Provider-Service Architecture (`providers/` and `models/`) separating Model Execution Mode (`hosted` vs `local`) from Research Security Mode (`baseline`, `prompt-only`, `guardrail`).
- **Decision Outcome**: Option 2.
  - Main LLM: `openai/gpt-oss-120b` on Groq (Hosted) and configurable Ollama (Local).
  - Embeddings: `gemini-embedding-2` (dim: 768) via Google GenAI SDK across both modes.
  - Prompt Injection: `meta-llama/llama-prompt-guard-2-86m` via Groq API across both modes.
  - Preserved: Presidio PII masking, custom regex & Shannon entropy secret detection, access control (RBAC), context delimiter framing, and secret leakage output interception.
- **Consequences**:
  - Positive: Produces 6 independent experiment configurations for research papers; keeps laptop memory footprint minimal under 8 GB RAM; strictly aligns with required model assignments.
  - Negative: Requires valid API keys for Gemini and Groq in both modes.
