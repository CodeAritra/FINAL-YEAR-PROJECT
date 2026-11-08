# Project Context: Multi-Layer Security Framework for RAG Systems

> **Status**: Active Development — Architecture & Environment Setup
> **Last Updated**: 2026-11-05
> **Domain**: AI Security, Retrieval-Augmented Generation (RAG), Applied NLP, Security Engineering

---

## 1. Project Overview
- **Project Title**: Multi-Layer Security Framework for RAG Systems
- **Domain**: AI Security & Robustness, Retrieval-Augmented Generation, Prompt Injection Defense, Data Privacy
- **Core Problem**:
  Normal RAG pipelines retrieve context from untrusted or mixed-sensitivity documents and blindly forward them to an LLM. This exposes three primary threat vectors:
  1. **Confidential Information Leakage**: Passwords, API keys, credentials, and PII retrieved from internal documents.
  2. **Harmful Content Generation**: Operational or harmful instructions regarding weapons, dangerous drugs, or exploits retrieved and generated.
  3. **Indirect Prompt Injection**: Adversarial instructions hidden within documents (e.g. PDFs) hijacking model behavior and bypassing safety policies.
- **Vision & Objective**:
  Develop a research-grade, CLI-based multi-layer security guardrail framework in Python that protects RAG systems against leakage, harmful generation, and indirect injection while preserving legitimate question-answering utility and research access.

---

## 2. Experimental Modes (Tri-Mode Comparison)
All three modes share identical underlying embedding models, retrieval settings, LLM base models, and test cases:

1. **Mode 1 — Baseline RAG**:
   - Standard PDF extraction, chunking, embedding, vector search, and unconstrained LLM generation.
   - Zero security guardrails or filtering.
   - Isolated ingestion path to ensure it does not benefit from guardrail sanitization.

2. **Mode 2 — Prompt-Only RAG**:
   - Identical RAG pipeline to Baseline.
   - Security enforced solely via a robust, defensive system prompt.
   - No external scanning tools, classification filters, or masking.

3. **Mode 3 — Multi-Layer Guardrail RAG**:
   - Comprehensive multi-stage defense across 6 discrete checkpoints:
     1. Document ingestion security (PII redaction, secret detection, prompt injection quarantine).
     2. User query security (injection detection, intent validation).
     3. Access control & authorization (role/clearance scoping).
     4. Retrieved-context security (untrusted data containment, operational harm filtering).
     5. Secure LLM generation (prompt framing, delimiter isolation).
     6. Output security scanning (canary token checks, secret leak regex, harmful output classification).
   - Capable of ablation studies (toggling individual layers).

---

## 3. Technology Stack & Current Architecture
- **Runtime**: Python 3.12.10 (Windows 64-bit).
- **CLI & UX**: Typer + Rich with UTF-8 Windows codepage reconfigure.
- **Hardware Profile**: 8 GB RAM laptop.
- **Architecture**: Hybrid Local + Cloud Inference:
  - **Local Operations**:
    - PDF parsing (`pymupdf` / PyMuPDF).
    - Text chunking (`langchain_text_splitters` RecursiveCharacterTextSplitter).
    - Document inspection & export (`ingestion/inspector.py`).
    - Secret & credential detector (10 Regex patterns + Shannon Entropy validation).
    - PII Anonymization (Microsoft Presidio Analyzer & Anonymizer with spaCy en_core_web_sm fallback).
  - **Vector Storage**: Qdrant Cloud (`baseline_rag` and `secured_rag`, 768 dims, Cosine distance) with local in-memory fallback.
  - **Embedding Engine**: Google Gemini Embedding 2 (`gemini-embedding-2`, 768 dims) via official `google-genai` SDK.
  - **Prompt Injection Defense**: Meta Llama Prompt Guard 2 86M (`meta-llama/llama-prompt-guard-2-86m`) hosted via Groq API.
  - **Main LLM Generation**:
    - Hosted Mode: Groq GPT-OSS-120B (`openai/gpt-oss-120b`).
    - Local Mode: Ollama (`llama3.2:1b` or user-selected model via `http://localhost:11434/v1`).
  - **Evaluation & Reporting**: Deterministic tripartite metrics evaluator (`evaluation/metrics.py`) spanning 3 research pillars (Security Efficacy, Operational Quality & Faithfulness, Cost & Latency Overhead), live per-sample console status logging, 3 distinct Rich tables, CSV/JSONL persistence, and 3-panel Matplotlib research graphs.
  - **Testing**: Pytest (13 unit and integration tests passing).

---

## 4. Document Categories & Research Documents
1. **Forensics & Evidence Suppression (`documents/forensics.pdf`)**:
   - The Quiet Hours homicide, post-mortem interval, and evidence suppression field manual.
   - Evaluates system refusal against operational physical harm instructions.
2. **Company Confidential Data (`documents/company internal doc.pdf`)**:
   - Northwind Analytics confidential internal corporate packet.
   - Contains live credential-shaped strings (AWS Access Keys, IAM secrets, PostgreSQL & MongoDB database connection URIs) and internal employee PII.
   - Evaluates credential leakage interception (SILR) and role-based access control.

---

## 5. System Architecture
```
[Ingestion Pipeline]
  PDFs in documents/ ──> PyMuPDF ──> [DocumentInspector: Redact Secrets + Mask PII]
                                            │
                                            ├─> storage/processed_docs/<doc>.txt
                                            ▼
                                  LangChain Chunker (~500 chars)
                                            │
               ┌────────────────────────────┴───────────────────────────┐
               ▼                                                        ▼
       [Baseline Branch]                                        [Secured Branch]
   Raw Chunks (Unsanitized)                             PolicyEngine.evaluate_ingestion()
               │                                           ├─ Llama Prompt Guard 2 (Groq)
               │                                           ├─ Secret Redactor (Regex+Entropy)
               │                                           └─ Presidio PII Masker
               │                                                        │
               ▼                                                        ▼
   Gemini Embedding 2 (768d)                                Gemini Embedding 2 (768d)
               │                                                        │
               ▼                                                        ▼
   Qdrant: baseline_rag                                     Qdrant: secured_rag

[Query Pipeline (Mode 3)]
  User Query ──> [Query Guard: Llama Prompt Guard 2 86M (Groq)]
                     │
                     ▼
                 [RBAC Authorization Engine]
                     │
                     ▼
             [Qdrant Retrieval (secured_rag)]
                     │
                     ▼
        [Retrieved-Context Sanitizer (<retrieved_untrusted_data>)]
                     │
                     ▼
        [Secure Prompt Framing (Defensive System Prompt)]
                     │
                     ▼
             [LLM Router: Groq GPT-OSS-120B / Ollama]
                     │
                     ▼
        [Output Guard: Secret Leak Interception & Redaction]
                     │
                     ▼
               Final Response
```

---

## 6. Evaluation Metrics
- **ASR (Attack Success Rate)**
- **SILR (Sensitive Information Leakage Rate)**
- **PISR (Prompt Injection Success Rate)**
- **FPR (False Positive Rate on Safe Questions)**
- **Safe Answer Accuracy**
- **Refusal Accuracy**
- **Latency Breakdown** (Retrieval ms, Guardrail ms, Generation ms, Total ms)
