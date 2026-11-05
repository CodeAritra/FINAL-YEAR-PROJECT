# Multi-Layer Security Framework for RAG Systems

A research-oriented framework and CLI platform designed to protect Retrieval-Augmented Generation (RAG) systems against **confidential information leakage**, **harmful operational content generation**, and **indirect prompt injection**.

---

## 1. Project Overview & Problem Statement

Standard RAG architectures blindly retrieve context from external documents and inject it into an LLM's prompt. This creates severe security vulnerabilities:

1. **Confidential Information Leakage**: Passwords, API keys, tokens, and employee PII embedded in documents are exposed to end users.
2. **Harmful Content Generation**: Operational instructions for dangerous materials (weapons, illegal drug synthesis) are retrieved and summarized.
3. **Indirect Prompt Injection**: Adversarial instructions hidden inside PDFs hijack the LLM's reasoning and bypass safety policies.

This framework implements and benchmarks **three independent RAG modes** side-by-side using identical models, retrieval configurations, and test cases:

- **Mode 1 — Baseline RAG**: Standard PDF extraction, chunking, embedding, vector search, and unconstrained LLM generation. Zero security guardrails.
- **Mode 2 — Prompt-Only RAG**: Same RAG pipeline, but protected solely by a defensive, security-focused system prompt. No external detection tools.
- **Mode 3 — Multi-Layer Guardrail RAG**: A comprehensive 6-stage defense architecture:
  1. *Ingestion Security*: Secret detection, Presidio PII masking, injection quarantine, and data sensitivity tiering.
  2. *Query Security*: Prompt injection detection (DeBERTa v3) and malicious intent classification.
  3. *Access Control (RBAC)*: Clearance enforcement across `ANONYMOUS`, `RESEARCHER`, `STAFF`, and `ADMIN`.
  4. *Retrieved-Context Security*: Neutralizing instructional prefixes and framing data in rigid `<retrieved_untrusted_data>` boundaries.
  5. *Secure LLM Generation*: Structured system prompt isolating instructions from untrusted data.
  6. *Output Security Scanning*: Intercepting leaked credentials and scanning output with Meta Llama Guard 3.

---

## 2. Directory Structure

```
code/
├── main.py                     # CLI entry point
├── config.py                   # Centralized configuration (Pydantic Settings)
├── requirements.txt            # Python dependencies
├── .env.example                # Template for environment variables and API keys
├── AGENTS.md                   # Multi-agent operating protocol and memory lifecycle
├── memory/                     # Persistent session memory
│   ├── context.md              # Project domain, architecture, and scope
│   ├── tasks.md                # Roadmap, current sprint, and backlog
│   ├── decisions.md            # Architecture Decision Records (ADRs)
│   ├── progress.md             # Chronological session logs
│   └── learnings.md            # Technical insights and debugging notes
├── cli/                        # Typer + Rich CLI application
│   └── app.py                  # Commands: ingest, ask, evaluate, report, status
├── database/                   # Vector database management
│   └── qdrant_manager.py       # Qdrant Cloud client with in-memory fallback
├── ingestion/                  # Document parsing and chunking
│   ├── pdf_extractor.py        # PyMuPDF text & metadata extraction
│   ├── chunker.py              # LangChain recursive character chunking
│   └── pipeline.py             # Separate baseline vs. secured ingestion
├── guardrails/                 # Individual security modules
│   ├── secret_detector.py      # Regex + Shannon entropy credential detection
│   ├── pii_masker.py           # Microsoft Presidio Analyzer & Anonymizer
│   ├── prompt_injection.py     # DeBERTa v3 Prompt Injection v2 client + heuristics
│   ├── harm_classifier.py      # Llama Guard 3 client + operational filters
│   ├── access_control.py       # Role-Based Access Control (RBAC) & clearances
│   └── context_sanitizer.py    # Delimiter wrapping & instruction stripping
├── policies/                   # Central decision engine
│   └── engine.py               # Explicit ALLOW / REDACT / QUARANTINE / BLOCK & ablations
├── modes/                      # The 3 comparative RAG systems
│   ├── baseline.py             # Mode 1: Baseline RAG
│   ├── prompt_only.py          # Mode 2: Prompt-Only RAG
│   └── guardrail.py            # Mode 3: Multi-Layer Guardrail RAG
├── evaluation/                 # Automated benchmarking & reporting
│   ├── test_case.py            # Dataset loader and schema
│   ├── metrics.py              # Deterministic metric evaluators (ASR, SILR, PISR, FPR)
│   ├── evaluator.py            # Multi-mode automated benchmark runner
│   └── reporting.py            # Rich comparison tables + Matplotlib charts
└── tests/                      # Automated unit and integration test suite
```

---

## 3. Quick Start & Setup Guide

### Step 1: Environment & Virtual Environment

Ensure you have **Python 3.11 or 3.12** installed:

```bash
# Check Python version
python --version

# The virtual environment is already created at .venv.
# To activate it:
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (Command Prompt):
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate
```

If setting up on a new machine from scratch:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

### Step 2: Configure Environment Variables (`.env`)

Copy `.env.example` to `.env`:

```bash
copy .env.example .env   # On Windows
cp .env.example .env     # On Linux / macOS
```

Open `.env` and fill in your connection details:

```ini
# --- Vector Database (Qdrant Cloud) ---
QDRANT_URL=https://your-cluster-id.us-east4-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-cloud-api-key

# --- Primary LLM Provider (Virtual GPU / Hosted / Ollama) ---
LLM_PROVIDER=openai_compatible     # or ollama_cloud | local_ollama | mock
LLM_MODEL=qwen2.5:7b
LLM_BASE_URL=https://your-virtual-gpu-endpoint/v1
LLM_API_KEY=your-llm-api-key

# --- Prompt Injection Classifier (ProtectAI DeBERTa v3) ---
PROMPT_INJECTION_PROVIDER=mock     # or hosted_hf
HF_API_KEY=your-huggingface-api-key

# --- Harmful Content Classifier (Meta Llama Guard 3 1B) ---
LLAMA_GUARD_PROVIDER=mock          # or hosted_api
LLAMA_GUARD_API_URL=https://your-virtual-gpu-endpoint/v1
LLAMA_GUARD_API_KEY=your-api-key
```

> **Note**: If API keys are omitted or set to `mock`, the system automatically runs deterministic local mock generators so all commands, tests, and workflows execute offline.

---

### Step 3: Verify System Status

Run the diagnostics command to verify your configuration and connections:

```bash
python main.py status
```

---

## 4. How to Use the CLI

### 1. Ingest Documents
Place your research PDFs into a folder (e.g., `documents/`) and run:
```bash
# Ingest into both baseline and secured collections
python main.py ingest --folder documents/

# Or target a specific collection
python main.py ingest --folder documents/ --target secured
```

### 2. Query the Systems
Ask questions across the three comparative modes:

```bash
# Mode 1: Baseline RAG (no guardrails)
python main.py ask --mode baseline --query "What are the database credentials?"

# Mode 2: Prompt-Only RAG (defensive prompt)
python main.py ask --mode prompt-only --query "What are the database credentials?"

# Mode 3: Multi-Layer Guardrail RAG (full defense pipeline)
python main.py ask --mode guardrail --query "What are the database credentials?" --role RESEARCHER
```

### 3. Run Automated Evaluation Benchmark
Once your evaluation dataset (`.json` or `.jsonl`) is ready:

```bash
# Run full benchmark comparing Baseline vs. Prompt-Only vs. Guardrail
python main.py evaluate --dataset path/to/eval_dataset.json --all

# Run ablation experiments (disabling one layer to measure its contribution)
python main.py evaluate --dataset path/to/eval_dataset.json --ablate ingestion
python main.py evaluate --dataset path/to/eval_dataset.json --ablate query
python main.py evaluate --dataset path/to/eval_dataset.json --ablate context
python main.py evaluate --dataset path/to/eval_dataset.json --ablate output
```

### 4. View Research Reports & Generated Charts
```bash
python main.py report
```
Visual bar charts comparing Attack Success Rate (ASR), Info Leakage (SILR), Prompt Injection (PISR), False Positive Rate (FPR), and Latency are saved as publication-ready PNGs in `storage/eval_results/`.

### 5. Run Automated Tests
```bash
pytest tests/
```

---