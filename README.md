# Multi-Layer Security Framework for RAG Systems

A research-oriented framework and CLI platform designed to protect Retrieval-Augmented Generation (RAG) systems against **confidential information leakage**, **harmful operational content generation**, and **indirect prompt injection**.

---

## 1. AI Models & Responsibilities

The architecture strictly separates model duties to ensure reproducibility, rigorous security evaluation, and lightweight resource usage:

| Responsibility | Model | Provider | Function |
|---|---|---|---|
| **Main Answer Generation (Hosted)** | `openai/gpt-oss-120b` | Groq API | Cloud-hosted generation via Groq. |
| **Main Answer Generation (Local)** | Configurable (e.g. `llama3.2:1b`) | Local Ollama | Local LLM inference designed for 8 GB RAM laptop limits. |
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
├── run_eval.py                 # Quick runner for balanced 50 & 100 benchmark evaluations
├── config.py                   # Central settings forwarder
├── requirements.txt            # Python dependencies (google-genai, groq, typer, etc.)
├── .env.example                # Template for environment credentials
├── documents/                  # Research PDFs for evaluation
│   ├── forensics.pdf           # Forensics & operational harm testing document
│   └── company internal doc.pdf# Internal corporate data & credential leaks document
├── evaluation/                 # Automated benchmarking & reporting
│   ├── datasets/               # Dedicated evaluation benchmark datasets
│   │   ├── balanced_50_benchmark.json          # 50-question balanced cross-PDF benchmark (no skew)
│   │   ├── balanced_100_benchmark.json         # 100-question balanced cross-PDF benchmark (no skew)
│   │   ├── forensics_100_benchmark.json        # 100 questions from forensics.pdf
│   │   ├── company_100_benchmark.json          # 100 questions from company internal doc.pdf
│   │   └── full_200_benchmark.json             # Combined 200-question master dataset
│   ├── test_case.py            # Dataset loader and schema
│   ├── metrics.py              # Deterministic metric evaluators (ASR, SILR, PISR, FPR)
│   ├── evaluator.py            # Multi-mode automated benchmark runner
│   └── reporting.py            # Rich comparison tables + Matplotlib charts + Markdown reports
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
│   ├── inspector.py            # Pre-chunking extraction & sanitization exporter (.txt)
│   └── pipeline.py             # Separate baseline vs. secured ingestion collections
├── scripts/                    # Standalone administration utilities
│   ├── clean_qdrant.py         # Qdrant collection purge and reset tool
│   ├── build_balanced_benchmarks.py # Generates balanced 50 & 100 question non-skewed test suites
│   └── build_dataset.py        # Benchmark dataset validator, statistics & merge tool
├── storage/                    # Persistent runtime artifacts
│   ├── processed_docs/         # Sanitized document exports (one .txt per PDF)
│   └── eval_results/           # Benchmark reports (.md, .jsonl, .csv, and .png comparison charts)
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
Ingests PDFs from `documents/` into Qdrant Cloud, creating matching 768-dimensional collections:
```bash
# Ingest both forensics.pdf and company internal doc.pdf
python main.py ingest --folder documents/

# Or ingest into secured collection only
python main.py ingest --folder documents/ --target secured
```

### 2. Inspect Sanitized Documents (Pre-Chunking Audit)
Extracts full text from PDFs, evaluates Secret Redaction and Presidio PII Masking, and exports one readable `.txt` file per PDF to `storage/processed_docs/`:
```bash
# Inspect and export sanitized text for all PDFs in documents/
python main.py inspect --folder documents/

# Output files generated in storage/processed_docs/:
# - storage/processed_docs/company internal doc.txt (with AWS keys & DB URIs redacted)
# - storage/processed_docs/forensics.txt
```

### 3. Clean / Reset Qdrant Database
Purges points and resets vector collections (`baseline_rag`, `secured_rag`, or all collections) in Qdrant Cloud:
```bash
# Reset baseline and secured collections and recreate fresh empty collections
python main.py clean

# Or run the standalone cleanup script
python scripts/clean_qdrant.py

# Clean only baseline collection
python main.py clean --target baseline

# Clean without interactive confirmation prompt
python main.py clean --force

# Purge ALL collections in cluster (with immediate recreation)
python scripts/clean_qdrant.py --all --recreate --force
```

### 4. Querying Across Modes (6 Combinations)

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

### 5. Automated Benchmark Evaluation
Runs test cases across all three security modes with live real-time progress logging for every sample.

#### Recommended: Balanced Non-Skewed Benchmark Runner
Executes balanced questions selected equally across **both PDFs** (Forensics + Company) with a strict 50% answerable and 50% unanswerable distribution (including password theft, harmful requests, and safe inquiries):

```bash
# Run quick balanced 20-question benchmark (PDF1: 5 safe/5 harmful; PDF2: 5 safe/5 restricted with 3 secret extractions)
python run_eval.py 20

# Run balanced 50-question benchmark (PDF1: 13 safe/12 harmful; PDF2: 12 safe/13 restricted with 8 secret extractions)
python run_eval.py 50

# Run balanced 100-question benchmark (PDF1: 25 safe/25 harmful; PDF2: 25 safe/25 restricted with 10 secret extractions)
python run_eval.py 100

# Run balanced benchmark using Local LLM (Ollama)
python run_eval.py 20 --model-mode local
```

#### Detailed CLI Evaluation Commands:

```bash
# Evaluate 10 balanced questions (5 answerable, 5 unanswerable) on Forensics
python main.py evaluate --target forensics --sample 10

# Evaluate 50 balanced questions (25 answerable, 25 unanswerable) on Company Confidential document
python main.py evaluate --target company --sample 50

# Evaluate all questions across both documents (combined benchmark)
python main.py evaluate --target all --sample all

# Default evaluation (runs the active benchmark suite across all 3 security modes)
python main.py evaluate

# Quick evaluation on first N test cases
python main.py evaluate --limit 5

# Custom dataset override
python main.py evaluate --dataset evaluation/datasets/balanced_50_benchmark.json --model-mode hosted --all

# Benchmark using Local LLM Mode (Ollama)
python main.py evaluate --model-mode local --all

# Benchmark BOTH Hosted and Local modes (all 6 configurations in one run)
python main.py evaluate --model-mode all --all

# Ablation Experiments: disable a single security layer to measure its contribution
python main.py evaluate --ablate ingestion
python main.py evaluate --ablate query
python main.py evaluate --ablate context
python main.py evaluate --ablate output
```

#### Evaluation Flags Reference
| Flag | Short | Default | Description |
|---|---|---|---|
| `--target` | `-t` | `all` | Document dataset: `forensics`, `company`, or `all`. |
| `--sample` | `-s` | `all` | Balanced sample size: `10` (5 ans / 5 unans), `50` (25 ans / 25 unans), or `all`. |
| `--dataset`| `-d` | None | Direct path override to any custom `.json` or `.jsonl` benchmark file. |
| `--model-mode` | `-M` | `hosted` | LLM execution mode: `hosted` (Groq 120B), `local` (Ollama), or `all` (both). |
| `--all` | | `True` | Automatically runs across all 3 security modes (Baseline, Prompt-Only, Guardrail). |
| `--limit` | `-n` | None | Limits evaluation to first N test cases. |
| `--ablate`| | None | Ablation study: disables `ingestion`, `query`, `context`, or `output` layer. |

Every run outputs:
- **Live console progress**: Showing global progress `(XX/YY)`, mode badge, question preview, result status (`[REFUSED / PROTECTED]`, `[ATTACK SUCCEEDED]`, `[SECRET LEAKED]`, `[SAFE ANSWER]`), and exact latency in milliseconds.
- **Tripartite Terminal Benchmark Reports**: Displays 3 distinct Rich tables (Security Efficacy, Operational Quality, and Latency Overhead).
- **Markdown Evaluation Report**: Saved to `storage/eval_results/eval_run_<timestamp>.md` with all tables and metrics.
- **Excel-ready CSV**: Saved to `storage/eval_results/eval_run_<timestamp>.csv`
- **JSONL Full Audit Trail**: Saved to `storage/eval_results/eval_run_<timestamp>.jsonl`
- **Publication Comparison Charts**: Rendered to `storage/eval_results/comparison_chart_<timestamp>.png` (3-panel figures).
- **Excel-ready CSV**: Saved to `storage/eval_results/eval_run_<timestamp>.csv`
- **JSONL Full Audit Trail**: Saved to `storage/eval_results/eval_run_<timestamp>.jsonl`
- **Publication Comparison Charts**: Rendered to `storage/eval_results/comparison_chart_<timestamp>.png` (3-panel figures).

---

### 6. Research Metrics & The Tripartite Evaluation Paradigm

In security research, evaluating threat mitigation alone creates an **over-defense bias**: a system that refuses 100% of queries is theoretically 100% secure, but completely useless in production.

To provide a rigorous academic defense and publication-ready evaluation, this framework measures the **Triad of RAG Systems** across three complementary pillars:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   THE TRIPARTITE RAG RESEARCH EVALUATION PARADIGM                │
├──────────────────────────┬───────────────────────────┬───────────────────────────┤
│   Pillar 1: Security     │   Pillar 2: Operational   │     Pillar 3: Cost &      │
│        Efficacy          │   Quality & Faithfulness  │     Latency Overhead      │
│   (Threat Mitigation)    │       (RAG Utility)       │  (Operational Feasibility)│
├──────────────────────────┼───────────────────────────┼───────────────────────────┤
│ • Attack Success (ASR)   │ • Safe Answer Accuracy    │ • Retrieval Latency (ms)  │
│ • Secret Leakage (SILR)  │ • Context Hit Rate (Hit@4)│ • Generation Latency (ms) │
│ • Prompt Injection (PISR)│ • Faithfulness (Grounded) │ • Guardrail Overhead (ms) │
│ • False Positive (FPR)   │ • Parametric Leakage Rate │ • Total Pipeline Latency  │
│ • Refusal Accuracy       │ • Over-Defense Rate (ODR) │ • Mean Cosine Vector Score│
└──────────────────────────┴───────────────────────────┴───────────────────────────┘
```

#### Pillar 1: Security Efficacy (Threat Mitigation)
Measures how effectively each mode blocks malicious, adversarial, or exfiltration attempts.

| Metric | Definition & Formula | Academic Importance & Target |
|---|---|---|
| **Attack Success Rate (ASR) ↓** | $\frac{\text{Successful Attacks}}{\text{Total Adversarial Queries}} \times 100$ | **Primary defense metric**: Proves whether malicious instructions (harmful requests, injections, extractions) were executed. Baseline is typically $>90\%$; Guardrail must achieve **$0.0\%$**. |
| **Sensitive Info Leakage (SILR) ↓** | $\frac{\text{Queries Leaking Secrets}}{\text{Total Secret Probes}} \times 100$ | **Confidentiality metric**: Measures whether API keys, staging credentials, or PII were disclosed. Target: **$0.0\%$**. |
| **Prompt Injection Rate (PISR) ↓** | $\frac{\text{Successful Jailbreaks}}{\text{Total Injection Probes}} \times 100$ | **Integrity metric**: Measures whether indirect injection delimiters, DAN personas, or system overrides were obeyed. Target: **$0.0\%$**. |
| **False Positive Rate (FPR) ↓** | $\frac{\text{Improperly Refused Safe Queries}}{\text{Total Safe Queries}} \times 100$ | **Precision metric**: Measures collateral damage—benign questions that were accidentally blocked by security filters. Target: **$< 3.0\%$**. |
| **Refusal Accuracy ↑** | $\frac{\text{Correctly Refused Threat Queries}}{\text{Total Threat Queries}} \times 100$ | **Safety compliance**: Proves the LLM or security filter generated a clear, unambiguous safety refusal when prompted with dangerous requests. Target: **$100\%$**. |

#### Pillar 2: Operational Quality & Faithfulness (RAG Utility)
Proves that adding multi-layer security **does not degrade** normal document-answering capabilities or introduce hallucinations.

| Metric | Definition & Formula | Academic Importance & Target |
|---|---|---|
| **Safe Answer Accuracy ↑** | $\frac{\text{Accurate Safe Answers}}{\text{Total Safe Queries}} \times 100$ | **Core utility metric**: Proves normal users continue getting correct, high-quality answers when asking legitimate questions. Target: **$> 90\%$**. |
| **Context Hit Rate (Hit@4) ↑** | $\frac{\text{Queries with Relevant Chunks in Top-4}}{\text{Total Queries}} \times 100$ | **Retrieval quality**: Verifies that Gemini Embedding 2 and Qdrant actually retrieved snippets from the ground-truth document section/page. Target: **$> 85\%$**. |
| **Context Faithfulness (Groundedness) ↑** | $\frac{\text{Answer Content Tokens Grounded in Chunks}}{\text{Total Answer Content Tokens}} \times 100$ | **Anti-hallucination metric**: Measures whether claims in the answer are strictly backed by retrieved text or invented. Guardrail's `<retrieved_untrusted_data>` delimiter achieves higher faithfulness than Baseline (**$> 90\%$**). |
| **Parametric Leakage Rate ↓** | $\frac{\text{Unanswerable Queries Answered from Weights}}{\text{Total Unanswerable Queries}} \times 100$ | **Parametric isolation**: When an answer is absent from the document, does the LLM answer from internal pre-training weights instead of stating the document lacks the fact? Target: **$< 5.0\%$**. |
| **Over-Defense Rate (ODR) ↓** | $\frac{\text{Safe Queries Rejected by Guardrails}}{\text{Total Safe Queries}} \times 100$ | **Usability penalty**: Identifies if the security layer became overly paranoid and disrupted standard business workflows. Target: **$< 2.0\%$**. |

#### Pillar 3: Performance, Cost & Latency Overhead (Operational Feasibility)
Proves that the security architecture is lightweight and deployable in production on standard cloud APIs or 8 GB RAM laptops.

| Metric | Definition & Measurement | Academic Importance & Target |
|---|---|---|
| **Retrieval Latency (ms)** | Time spent generating embeddings via Gemini API and querying Qdrant Cloud. | Constant across modes (~150–250 ms); isolates vector search performance. |
| **Generation Latency (ms)** | Time spent in LLM token inference (Groq GPT-OSS-120B or local Ollama). | Measures inference speed (~600–1200 ms). Attacks refused early have significantly lower generation latency. |
| **Guardrail Overhead Latency (ms)** | $\text{Latency}_{\text{Total}} - (\text{Latency}_{\text{Retrieval}} + \text{Latency}_{\text{Generation}})$ | **Critical engineering metric**: Measures the exact millisecond cost of Llama Prompt Guard 2, regex scanning, RBAC, and Presidio PII checks. Typically only **15–35 ms**. |
| **Total Pipeline Latency (ms)** | Complete wall-clock turnaround time from user query to verified response. | Confirms end-to-end responsiveness is acceptable for real-time human interaction ($< 1.5$ s). |
| **Mean Vector Score** | Average cosine similarity of top-K retrieved snippets. | Reflects dense embedding retrieval confidence in Qdrant. |

---

### 7. Benchmark Dataset Management Utilities
Inspect, validate, and merge dataset benchmark files:

```bash
# View summary table of all benchmark datasets (totals, answerable vs unanswerable breakdown)
python scripts/build_dataset.py stats

# Validate schema compliance and integrity of a specific benchmark file
python scripts/build_dataset.py validate --path evaluation/datasets/full_evaluation_benchmark.json

# Merge Forensics and Company datasets into a unified benchmark (full_200_benchmark.json)
python scripts/build_dataset.py merge
```

---

### 8. View Research Reports & Graphs
```bash
python main.py report
```
Displays recent benchmark summaries and outputs the path to the latest comparison charts.

---

### 9. Run Automated Tests
```bash
pytest tests/ -v
```
*(All 13 unit and integration tests validate provider routing, 768-dim embeddings, Prompt Guard rate-limiting, security modes, and dataset builder utilities).*
