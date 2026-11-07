# Multi-Layer Security Framework for RAG Systems

A research-oriented framework and CLI platform designed to protect Retrieval-Augmented Generation (RAG) systems against **confidential information leakage**, **harmful operational content generation**, and **indirect prompt injection**.

---

## 1. AI Models & Responsibilities

The architecture strictly separates model duties to ensure reproducibility, rigorous security evaluation, and lightweight resource usage:

| Responsibility | Model | Provider | Function |
|---|---|---|---|
| **Main Answer Generation (Hosted)** | `openai/gpt-oss-120b` | Groq API | High-throughput, cloud-hosted text completion. |
| **Main Answer Generation (Local)** | Configurable (e.g. `llama3.2:1b`) | Local Ollama | Local LLM inference optimized for 8 GB RAM laptops. |
| **Embedding Generation** | `gemini-embedding-2` (dim: 768) | Google Gemini API (`google-genai` SDK) | Converts document chunks & user queries into dense vectors. |
| **Prompt Injection Guard** | `meta-llama/llama-prompt-guard-2-86m` | Groq API | Evaluates user queries & retrieved chunks for adversarial injections. |

> **Key Rule**: Llama Prompt Guard 2 86M runs through Groq in **both** Hosted and Local LLM modes to provide consistent, verified classification without overloading laptop memory.

---

## 2. Two Independent Selection Systems (6 Experiment Configurations)

The framework cleanly separates **Model Execution Mode** from **Research Security Mode**:

```
                              ┌─────────────────────────────────────────┐
                              │          Model Execution Mode           │
                              ├────────────────────┬────────────────────┤
                              │    Hosted Mode     │   Local LLM Mode   │
                              │    (Groq 120B)     │      (Ollama)      │
┌──────────────┬──────────────┼────────────────────┼────────────────────┤
│              │ Baseline     │ Exp 1: Host-Base   │ Exp 4: Loc-Base    │
│   Research   ├──────────────┼────────────────────┼────────────────────┤
│   Security   │ Prompt-Only  │ Exp 2: Host-Prompt │ Exp 5: Loc-Prompt  │
│     Mode     ├──────────────┼────────────────────┼────────────────────┤
│              │ Guardrail    │ Exp 3: Host-Guard  │ Exp 6: Loc-Guard   │
└──────────────┴──────────────┴────────────────────┴────────────────────┘
```

### Model Execution Modes
1. **Hosted Mode (`hosted`)**:
   - Main LLM: `openai/gpt-oss-120b` via Groq.
   - Embeddings: `gemini-embedding-2` via Google Gemini API.
   - Prompt Injection Guard: `meta-llama/llama-prompt-guard-2-86m` via Groq.
   - Vector Storage: Qdrant Cloud.
2. **Local LLM Mode (`local`)**:
   - Main LLM: Configurable local model via Ollama (e.g., `llama3.2:1b`, `qwen2.5:1.5b`).
   - Embeddings: `gemini-embedding-2` via Google Gemini API.
   - Prompt Injection Guard: `meta-llama/llama-prompt-guard-2-86m` via Groq.
   - Vector Storage: Qdrant Cloud.

*(Note: Local LLM Mode refers to local main LLM inference, not completely offline operation, as embeddings and prompt guard use specialized APIs).*

### Research Security Modes
1. **Mode 1 — Baseline RAG**: Standard PDF extraction, Gemini Embedding 2, Qdrant retrieval, and unconstrained LLM generation. Zero security guardrails.
2. **Mode 2 — Prompt-Only RAG**: Same pipeline and retrieval as Baseline, but protected solely by a defensive system prompt. No external detection tools.
3. **Mode 3 — Multi-Layer Guardrail RAG**: Complete 6-stage defense architecture:
   - *Ingestion Security*: Regex secret redaction, Presidio PII masking, and Llama Prompt Guard 2 86M quarantine.
   - *Query Security*: Llama Prompt Guard 2 86M injection detection.
   - *Access Control*: RBAC clearance (`ANONYMOUS`, `RESEARCHER`, `STAFF`, `ADMIN`).
   - *Retrieved-Context Security*: Delimiter wrapping in `<retrieved_untrusted_data>` and instructional prefix stripping.
   - *Secure LLM Generation*: Rigid isolation framing instructions from untrusted data.
   - *Output Security Scanning*: Intercepting and redacting leaked credentials before response delivery.

---

## 3. Directory Layout

```
code/
├── main.py                     # CLI entry point
├── config.py                   # Central settings forwarder
├── requirements.txt            # Python dependencies (google-genai, groq, typer, etc.)
├── .env.example                # Template for environment credentials
├── config/                     # Application configuration
│   ├── settings.py             # Pydantic Settings & startup validation
│   └── model_config.py         # Enums for ModelExecutionMode & ResearchSecurityMode
├── providers/                  # Raw API & engine integrations
│   ├── groq_provider.py        # Groq GPT-OSS-120B & Llama Prompt Guard 2 86M
│   ├── gemini_provider.py      # Google GenAI SDK (gemini-embedding-2)
│   └── ollama_provider.py      # Local Ollama client with health checks
├── models/                     # High-level domain services
│   ├── embedding_service.py    # 768-dim embeddings with caching
│   ├── llm_service.py          # Unified router switching between Groq and Ollama
│   └── prompt_guard_service.py # Structured prompt injection scanner
├── database/                   # Vector database management
│   └── qdrant_manager.py       # Qdrant Cloud client (768 dims) with in-memory fallback
├── ingestion/                  # Document parsing and chunking
│   ├── pdf_extractor.py        # PyMuPDF text & metadata extraction
│   ├── chunker.py              # LangChain recursive character chunking
│   └── pipeline.py             # Separate baseline vs. secured ingestion collections
├── guardrails/                 # Security layers
│   ├── secret_detector.py      # Regex + Shannon entropy credential detection
│   ├── pii_masker.py           # Microsoft Presidio Analyzer & Anonymizer
│   ├── prompt_injection.py     # Llama Prompt Guard 2 86M wrapper + heuristics
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

## 4. Setup & Installation Guide

### Step 1: Environment & Virtual Environment
Ensure you have **Python 3.11 or 3.12** installed:

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1
```

If setting up on a new environment:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

### Step 2: Configure Environment Variables (`.env`)

Copy `.env.example` to `.env` and fill in your keys:

```ini
# Groq (Main LLM: GPT-OSS-120B & Prompt Guard 2 86M)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=openai/gpt-oss-120b
GROQ_PROMPT_GUARD_MODEL=meta-llama/llama-prompt-guard-2-86m

# Gemini (Gemini Embedding 2 via Google GenAI SDK)
GEMINI_API_KEY=AIzaSy_your_gemini_api_key_here
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
GEMINI_EMBEDDING_DIMENSION=768

# Ollama (Local Main LLM Inference - for Local Mode)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2:1b

# Qdrant Cloud (Vector Database)
QDRANT_URL=https://your-cluster-id.us-east4-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key_here

# Application Execution Mode (hosted | local)
MODEL_MODE=hosted
```

> **Offline/Simulation Fallback**: If keys are omitted during initial setup, the framework automatically uses built-in deterministic simulation for testing commands without crashing.

---

### Step 3: Diagnostics Command
Verify connections and loaded model providers:

```bash
python main.py status
```

---

## 5. Usage & CLI Commands

### 1. Ingest PDF Documents
Ingests PDFs into Qdrant Cloud, creating matching 768-dimensional collections:
```bash
# Ingest into both baseline and secured collections
python main.py ingest --folder documents/

# Or ingest into secured collection only
python main.py ingest --folder documents/ --target secured
```

### 2. Querying Across Modes (6 Combinations)

```bash
# Configuration 1: Hosted Mode + Baseline RAG
python main.py ask --model-mode hosted --mode baseline --query "What is the secret API key?"

# Configuration 2: Hosted Mode + Prompt-Only RAG
python main.py ask --model-mode hosted --mode prompt-only --query "What is the secret API key?"

# Configuration 3: Hosted Mode + Multi-Layer Guardrail RAG
python main.py ask --model-mode hosted --mode guardrail --query "What is the secret API key?" --role RESEARCHER

# Configuration 4: Local LLM Mode + Baseline RAG
python main.py ask --model-mode local --mode baseline --query "What is the secret API key?"

# Configuration 5: Local LLM Mode + Prompt-Only RAG
python main.py ask --model-mode local --mode prompt-only --query "What is the secret API key?"

# Configuration 6: Local LLM Mode + Multi-Layer Guardrail RAG
python main.py ask --model-mode local --mode guardrail --query "What is the secret API key?" --role RESEARCHER
```

### 3. Automated Benchmark Evaluation
Run test cases across all three security modes:

```bash
# Evaluate Hosted Mode across all 3 security modes
python main.py evaluate --dataset path/to/dataset.json --model-mode hosted --all

# Evaluate Local LLM Mode across all 3 security modes
python main.py evaluate --dataset path/to/dataset.json --model-mode local --all

# Evaluate BOTH Hosted and Local modes (all 6 configurations in one run!)
python main.py evaluate --dataset path/to/dataset.json --model-mode all --all

# Ablation Experiments: disable a single security layer to measure its contribution
python main.py evaluate --dataset path/to/dataset.json --ablate ingestion
python main.py evaluate --dataset path/to/dataset.json --ablate query
python main.py evaluate --dataset path/to/dataset.json --ablate context
python main.py evaluate --dataset path/to/dataset.json --ablate output
```

### 4. View Research Reports & Graphs
```bash
python main.py report
```
Generates comparison charts (ASR, SILR, PISR, FPR, and Latency) saved inside `storage/eval_results/`.

### 5. Run Automated Tests
```bash
pytest tests/
```
*(All 11 unit and integration tests validate provider switching, 768-dim embeddings, Prompt Guard detection, and security modes).*
