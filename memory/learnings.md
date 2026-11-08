# Project Learnings & Knowledge Base

This file captures tricky bugs solved, quirks of third-party libraries, performance traps, edge-case behaviors, and valuable technical discoveries made while developing this project.

---

## Knowledge Index

| Category | Title | Date Added | Summary |
| :--- | :--- | :--- | :--- |
| Workspace | Antigravity File System & Hierarchical Rules | 2026-11-05 | Rules in `.agents/rules/` and `AGENTS.md` automatically load; skills follow progressive disclosure. |
| SDK / AI | google-genai EmbedContentResponse structure | 2026-11-07 | `EmbedContentResponse` uses `.embeddings[0].values`, not `.embedding.values`. |
| API / Rate Limit | Groq 429 Rate Limit Handling in Prompt Guard & LLM | 2026-11-07 | Parse `retry-after` & regex duration on 429; wait and retry instead of falling back to heuristic. |
| Evaluation / NLP | Conversational Refusal Pattern Matching in Benchmarks | 2026-11-08 | Match contractions (`can't`, `can’t`), apologetic openers (`I'm sorry, but`), and verb variants (`help`). |

---

## Logged Learnings

### LRN-001: Antigravity Customization Discovery & Directory Hierarchy
- **Context**: Setting up repository customizations on Windows.
- **Problem / Discovery**: Antigravity automatically discovers customizations under `.agents/` at repository root, in addition to hierarchical root `AGENTS.md`. Skills require a strict frontmatter format (`name` and `description`) to be discoverable and load via progressive disclosure.
- **Solution / Takeaway**: All skills must include lowercase hyphenated names and actionable descriptions stating *what* and *when* to activate. High-volume reference materials should be separated into `references/` directories within each skill.

### LRN-002: google-genai SDK v2 EmbedContentResponse Attribute Structure
- **Context**: Document ingestion and query embedding using the official `google-genai` SDK.
- **Problem / Discovery**: In `google.genai.types.EmbedContentResponse`, the vector field is `.embeddings` (a list of `ContentEmbedding` objects where each item has `.values: list[float]`), whereas older deprecated `google.generativeai` libraries used `.embedding.values`. Accessing `response.embedding` raised `'EmbedContentResponse' object has no attribute 'embedding'`.
- **Solution / Takeaway**: Safely check `hasattr(response, "embeddings") and response.embeddings` first (`response.embeddings[0].values`), with fallback to `response.embedding.values`.

### LRN-003: Groq 429 Rate Limit Retry vs Heuristic Fallback
- **Context**: Rapid scanning of document chunks during ingestion using Llama Prompt Guard 2 86M via Groq.
- **Problem / Discovery**: Groq free/standard tier enforces rate limits (30 RPM). Processing 83 chunks concurrently or in a tight loop hit HTTP 429. The previous code immediately fell back to the heuristic classifier rather than waiting.
- **Solution / Takeaway**: Implement `_extract_retry_delay` parsing `Retry-After`, `x-ratelimit-reset-*`, and JSON body `"try again in X.Xs"`. In `GroqProvider.check_prompt_injection` and `GroqProvider.generate`, retry up to 8 times with exponential/header-derived backoff and never fall back to heuristic solely on 429.

### LRN-004: Conversational Refusal Pattern Matching in Benchmarks
- **Context**: Evaluating LLM refusal behaviors against adversarial forensic and injection queries.
- **Problem / Discovery**: Commercial models (e.g. `openai/gpt-oss-120b` on Groq) frequently generate polite natural-language refusals like `"I’m sorry, but I can’t help with that."` with unicode curly apostrophes (`’`) and colloquial verb forms (`help`). The previous evaluator only checked formal strings like `\bi cannot fulfill\b`, falsely scoring valid refusals as attack successes.
- **Solution / Takeaway**: Expanded `REFUSAL_PHRASES` in `evaluation/metrics.py` to match unicode contractions (`can't|can’t`), apologetic openers (`I(?:'m|’m| am) sorry`), policy references, and declarative refusals. Re-scored benchmark datasets to reflect true accuracy.

