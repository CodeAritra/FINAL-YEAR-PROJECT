# Task Roadmap & Backlog

> **Current Milestone**: Milestone 2 — Evaluation Dataset Ingestion & Virtual GPU Connection
> **Last Updated**: 2026-11-05

---

## Phase 1: Environment & Project Scaffolding
- [x] Inspect Python runtime and system capabilities (Python 3.12.10 detected).
- [x] Create Python virtual environment (`.venv`).
- [x] Create modular directory structure (`cli/`, `ingestion/`, `database/`, `rag/`, `modes/`, `guardrails/`, `policies/`, `evaluation/`, `storage/`, `logs/`).
- [x] Create `requirements.txt` with locked lightweight dependencies and `.env.example`.
- [x] Establish centralized configuration module (`config.py` using `pydantic-settings`).

## Phase 2: Database & Core RAG Pipeline
- [x] Implement Qdrant Cloud client manager with collection setup (`baseline_docs` vs. `secured_docs`).
- [x] Implement embedding engine (`all-MiniLM-L6-v2` via `sentence-transformers` with CPU device setting and offline fallback).
- [x] Implement PDF extraction (`PyMuPDF`) and chunking (`LangChain`).
- [x] Build common LLM inference provider interface (supporting hosted Ollama, OpenAI-compatible APIs, and offline mock).

## Phase 3: Tri-Mode RAG Implementation
- [x] Build `Mode 1: Baseline RAG` (`modes/baseline.py`).
- [x] Build `Mode 2: Prompt-Only RAG` (`modes/prompt_only.py`) with defensive prompt engineering.
- [x] Build `Mode 3: Multi-Layer Guardrail RAG` framework (`modes/guardrail.py`).
- [x] Build Typer CLI (`main.py` and `cli/`) supporting `ask --mode [baseline|prompt-only|guardrail]`.

## Phase 4: Security Layers & Policy Engine
- [x] Layer 1: Ingestion security (Secret regex detector, Presidio PII masker, injection detector).
- [x] Layer 2: User query security (Prompt injection classifier, malicious intent filter).
- [x] Layer 3: Access control & authorization (Clearance levels, role filtering).
- [x] Layer 4: Retrieved-context scanner (Untrusted data isolation, operational hazard detection).
- [x] Layer 5: Secure prompt framing & system delimiters.
- [x] Layer 6: Output security scanner (Canary tokens, secret leakage scan, Llama Guard 3 integration).
- [x] Policy engine with explicit Allow / Redact / Quarantine / Block decisions and ablation support.

## Phase 5: Evaluation Framework & Research Reporting
- [x] Build automated evaluation runner (`evaluation/evaluator.py`).
- [x] Support custom deterministic metric evaluators (ASR, SILR, PISR, FPR, Latency).
- [x] Implement reporting generator (`evaluation/reporting.py`) generating comparison tables (Rich) and CSV/JSONL results with Matplotlib charts.
- [x] Build Pytest test suites validating detectors (`pytest tests/` passing).
- [x] Comprehensive root documentation created (`README.md`).

---

## What Is Left (Pending User Inputs & Next Steps)

1. **User Research PDFs**: Ingest user's actual PDFs (`python main.py ingest --folder documents/`).
2. **Environment Variables**: Configure `.env` with user's Qdrant Cloud cluster and Virtual GPU endpoints.
3. **User Evaluation Dataset**: Load user's evaluation questions (`.json` or `.jsonl`).
4. **Benchmark Execution**: Run `python main.py evaluate --dataset <path> --all` to gather comparative empirical data.
5. **Ablation Studies**: Run `--ablate [ingestion|query|context|output]` to measure layer contributions.
