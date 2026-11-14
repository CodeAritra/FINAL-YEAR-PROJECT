# Project Progress & Session Changelog

This document maintains a chronological record of sessions, deliverables completed, milestones achieved, and blockers encountered.

---

## Session Logs

### Session 001: 2026-11-05
- **Goal**: Establish the repository AI operating foundation, persistent memory framework, specialized roles, project rules, and reusable skills.
- **Completed**:
  - Configured root `AGENTS.md` governing multi-agent interactions and memory-first protocol.
  - Initialized `memory/` persistent state (`context.md`, `decisions.md`, `tasks.md`, `progress.md`, `learnings.md`).
  - Added modular rules in `.agents/rules/` covering code standards, git workflow, testing verification, and security.
  - Defined 5 specialized AI agent roles under `.agents/roles/`.
  - Implemented 4 reusable skills under `.agents/skills/` (`memory-sync`, `project-onboarding`, `verification-gate`, `architecture-decision`).
- **Decisions Logged**:
  - `ADR-001`: Persistent Multi-Agent Workspace Architecture.
- **Current Blocker / Next Step**:
  - Waiting for project details and context from the user to populate `memory/context.md` and initiate technical execution.



### Session 002: 2026-11-05
- **Goal**: Ingest full project requirements for "Multi-Layer Security Framework for RAG Systems" and initiate Phase 1 implementation.
- **Completed**:
  - Ingested problem statement, 3 experimental modes, hybrid architecture, 6-layer defense requirements, and evaluation metrics.
  - Verified Python 3.12.10 and pip 26.2.1 runtime.
  - Recorded ADR-002: Hybrid Architecture for Memory-Constrained Research Pipeline.
  - Formulated phased implementation roadmap in `memory/tasks.md`.
- **Current Action**: Creating project directories, virtual environment, and baseline configuration files.


### Session 003: 2026-11-05
- **Goal**: Complete foundational project implementation, verify test suite, and provide comprehensive setup guide and documentation.
- **Completed**:
  - Implemented all 3 RAG modes (`baseline.py`, `prompt_only.py`, `guardrail.py`).
  - Implemented 6 security guardrails (`secret_detector.py`, `pii_masker.py`, `prompt_injection.py`, `harm_classifier.py`, `access_control.py`, `context_sanitizer.py`).
  - Implemented central `PolicyEngine` with explicit `ALLOW`/`REDACT`/`QUARANTINE`/`BLOCK` decisions and ablation support.
  - Built ingestion pipeline separating `baseline_rag` and `secured_rag` Qdrant collections.
  - Implemented evaluation harness with deterministic metrics (ASR, SILR, PISR, FPR, Latencies) and Matplotlib comparison chart generation.
  - Verified test suite (`pytest tests/`) passing 6/6 tests.
  - Handled Windows codepage console output encoding for cross-platform reliability.
  - Authored comprehensive root [`README.md`](../README.md) detailing project purpose, directory layout, commands, and next steps.
- **Next Steps**: Awaiting user's research PDFs, virtual GPU / cloud credentials in `.env`, and evaluation dataset to execute live benchmarks.


### Session 004: 2026-11-05
- **Goal**: Implement two selectable model execution modes (Hosted Groq vs. Local Ollama), integrate Gemini Embedding 2 and Groq Llama Prompt Guard 2 86M, and remove obsolete Sentence Transformers and Llama Guard components.
- **Completed**:
  - Installed `google-genai` and `groq` SDKs.
  - Built modular provider layer: `providers/groq_provider.py`, `providers/gemini_provider.py`, `providers/ollama_provider.py`.
  - Built high-level model services: `models/embedding_service.py` (Gemini Embedding 2, 768 dimensions), `models/llm_service.py` (routes Groq vs. Ollama), `models/prompt_guard_service.py` (Llama Prompt Guard 2 86M on Groq).
  - Cleanly decoupled Model Execution Modes (`hosted` vs `local`) from Research Security Modes (`baseline`, `prompt-only`, `guardrail`), creating 6 distinct experiment configurations.
  - Retired obsolete `sentence-transformers` and `harm_classifier.py` / Llama Guard 3.
  - Updated `database/qdrant_manager.py` to support 768-dimensional collections and modern `query_points` API.
  - Added comprehensive test suite in `tests/test_two_execution_modes.py` (11/11 tests passing).
  - Updated CLI commands (`main.py ask --model-mode hosted|local --mode baseline|prompt-only|guardrail`, `evaluate --model-mode hosted|local|all`, `status`).
  - Updated `.env.example` and root `README.md`.
  - Recorded ADR-003 in `memory/decisions.md`.
- **Status**: Framework verified and ready for live keys, document ingestion, and benchmark datasets.


### Session 005: 2026-11-07
- **Goal**: Integrate user-provided research PDFs and establish structured evaluation benchmark datasets for testing the 3 RAG modes.
- **Completed**:
  - Verified user uploaded PDFs in `documents/`: `forensics.pdf` and `company internal doc.pdf`.
  - Created dedicated dataset folder: `evaluation/datasets/`.
  - Structured the 20 forensic operational harm benchmark questions into `evaluation/datasets/forensics_benchmark.json`.
  - Structured corporate confidential & secret extraction questions into `evaluation/datasets/company_confidential_benchmark.json`.
  - Created combined 25-sample benchmark suite: `evaluation/datasets/full_evaluation_benchmark.json`.
  - Verified dataset integrity with `DatasetLoader` (25/25 valid schema records).
- **Next Steps**: Ingest PDFs via `python main.py ingest --folder documents/` and execute automated benchmark comparison via `python main.py evaluate --dataset evaluation/datasets/full_evaluation_benchmark.json --all`.


### Session 006: 2026-11-07
- **Goal**: Resolve Groq 429 rate limit errors without heuristic fallback, and provide a database cleanup and reset utility for Qdrant.
- **Completed**:
  - Fixed Google GenAI SDK v2 `EmbedContentResponse` attribute mapping in `providers/gemini_provider.py` (`embeddings[0].values`).
  - Enhanced `providers/groq_provider.py` with `_extract_retry_delay` parsing `Retry-After`, `x-ratelimit-reset-*`, and JSON error body durations.
  - Implemented 429 retry backoff loop in both `check_prompt_injection` and `generate`, ensuring the system waits and retries without prematurely falling back to heuristics.
  - Created [`scripts/clean_qdrant.py`](../scripts/clean_qdrant.py) supporting selective or complete collection purges with point counts and automatic empty collection recreation.
  - Added `python main.py clean` Typer command to `cli/app.py`.
  - Documented clean command options in root [`README.md`](../README.md).
  - Recorded LRN-002 and LRN-003 in `memory/learnings.md`.


### Session 007: 2026-11-08
- **Goal**: Implement pre-chunking document inspection and sanitization export (`python main.py inspect`), fix conversational refusal regex matching in metrics evaluator, and provide live real-time test progress during evaluation runs.
- **Completed**:
  - Created [`ingestion/inspector.py`](../ingestion/inspector.py) extracting full text from PDFs, applying Secret Redaction and PII Masking, and generating structured `.txt` exports.
  - Added `python main.py inspect --folder documents/` CLI command to [`cli/app.py`](../cli/app.py).
  - Wired auto-export into [`ingestion/pipeline.py`](../ingestion/pipeline.py) so ingestion keeps `storage/processed_docs/` synchronized.
  - Enhanced [`evaluation/metrics.py`](../evaluation/metrics.py) refusal regex (`REFUSAL_PHRASES`) to accurately capture conversational contractions (`can't|can’t`), apologetic openers (`I'm sorry, but`), and verb variants (`help`).
  - Upgraded [`evaluation/evaluator.py`](../evaluation/evaluator.py) with live, per-sample terminal status logging showing progress counter `(XX/YY)`, mode badge, test ID, query preview, status badge (`[REFUSED / PROTECTED]`, `[ATTACK SUCCEEDED]`, `[SECRET LEAKED]`), and latency in ms.
  - Re-scored and regenerated all benchmark results in `storage/eval_results/`.
  - Added `--limit` / `-n` option to `python main.py evaluate` and set default dataset to `full_evaluation_benchmark.json`.


### Session 008: 2026-11-08
- **Goal**: Prepare benchmark expansion infrastructure, implement subset sampling flags (`--target` and `--sample 10/50/all`), build dataset management utilities (`scripts/build_dataset.py`), and synchronize all documentation and test suites.
- **Completed**:
  - Implemented `--target` (`forensics`, `company`, `all`) and balanced `--sample` (`10`, `50`, `all`) in [`cli/app.py`](../cli/app.py) with automatic 50/50 answerable vs. unanswerable balancing and fallback warnings for unexpanded sets.
  - Built [`scripts/build_dataset.py`](../scripts/build_dataset.py) CLI providing `stats` (table breakdown across all benchmark files), `validate` (integrity & schema validator), and `merge` (combines Forensics + Company into `full_200_benchmark.json`).
  - Added unit test suite [`tests/test_dataset_builder.py`](../tests/test_dataset_builder.py) verifying test case factories and validation logic (13/13 unit tests passing).
  - Synchronized root [`README.md`](../README.md) with comprehensive documentation for `--target`, `--sample`, dataset management tools, and live progress indicators.
  - Memory synchronized; system completely prepared for user's question set ingestion.


### Session 009: 2026-11-08
- **Goal**: Implement the Tripartite Evaluation Paradigm (Security Efficacy, Operational Quality & Faithfulness, Cost & Latency Overhead) across all 3 RAG modes and document metric formulas and importance.
- **Completed**:
  - Enhanced [`evaluation/metrics.py`](../evaluation/metrics.py) with full support for:
    - Context Hit Rate (Hit@K) tracking retrieval precision in Qdrant.
    - Context Faithfulness (Groundedness score) measuring answer token support against retrieved chunks.
    - Parametric Leakage Rate tracking when the LLM answers unanswerable queries from pre-trained weights.
    - Over-Defense Rate (ODR) measuring false refusals on safe questions.
    - Guardrail Overhead Latency measuring exact millisecond penalty of security filters.
    - Vector Cosine Similarity Score averaging.
  - Wired snippet extraction into [`evaluation/evaluator.py`](../evaluation/evaluator.py).
  - Upgraded [`evaluation/reporting.py`](../evaluation/reporting.py) to display 3 distinct Rich tables (Security Efficacy, Operational Quality, Cost & Latency) and generate 3-panel research charts.
  - Recorded ADR-004 in [`memory/decisions.md`](../memory/decisions.md).
  - Updated root [`README.md`](../README.md) with dedicated section explaining all metrics, formulas, targets, and academic relevance.
  - Verified 13/13 pytest suite passes and executed sample evaluation run.


### Session 011: 2026-11-11
- **Goal**: Ingest Batch 1 Forensics questions (Groups A through J), establish tripartite reporting, and author publication-grade `methodology.md`.
- **Completed**:
  - Ingested 50 Forensics questions across Groups A-J (`FORENSIC-001` to `FORENSIC-050`).
  - Authored publication-grade [`methodology.md`](../methodology.md).

### Session 015: 2026-11-12
- **Goal**: Implement automatic Markdown evaluation report generation (`eval_run_<timestamp>.md`) containing the 3 terminal tables and metric definitions.
- **Completed**:
  - Implemented `EvaluationReporter.generate_markdown_report` in [`evaluation/reporting.py`](../evaluation/reporting.py) generating formatted Markdown tables for Security Efficacy, Operational Quality & Groundedness, and Performance/Latency.
  - Updated [`cli/app.py`](../cli/app.py) to automatically produce the `.md` report alongside `.jsonl`, `.csv`, and `.png` on every benchmark run.
  - Generated `storage/eval_results/eval_run_20261112_084411.md` for the recent 50-sample evaluation run.
  - Verified 11/11 unit tests pass.

### Session 016: 2026-11-12
- **Goal**: Construct balanced, non-skewed 50-question and 100-question benchmarks combining PDF1 (Forensics) and PDF2 (Company) with secret extraction, harmful requests, and safe questions.
- **Completed**:
  - Built [`scripts/build_balanced_benchmarks.py`](../scripts/build_balanced_benchmarks.py) to generate `balanced_100_benchmark.json`, `balanced_50_benchmark.json`, and `balanced_20_benchmark.json`.
  - Balanced 100 questions: 25 Forensics safe + 25 Forensics harmful + 25 Company safe + 25 Company restricted (10 secret extraction + 15 HR/PII).
  - Balanced 50 questions: 13 Forensics safe + 12 Forensics harmful + 12 Company safe + 13 Company restricted (8 secret extraction + 5 HR/PII).
  - Balanced 20 questions: 5 Forensics safe + 5 Forensics harmful + 5 Company safe + 5 Company restricted (3 secret extraction + 2 HR/PII).
  - Created [`run_eval.py`](../run_eval.py) runner script allowing single-command evaluation execution (`python run_eval.py 20` / `50` / `100`).
