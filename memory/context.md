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

## 3. Technology Stack & Hardware Constraints
- **Runtime**: Python 3.12.10 (Windows 64-bit).
- **Hardware Profile**: 8 GB RAM laptop.
- **Architecture**: Hybrid Local + Cloud Inference:
  - **Local Operations**: Python CLI (Typer + Rich), PDF parsing (PyMuPDF), Text Chunking (LangChain text splitters), Secret regex detection, Presidio PII detection, sentence-transformers (all-MiniLM-L6-v2).
  - **Vector Storage**: Qdrant Cloud (managed via URL + API Key).
  - **Cloud Inference (Lightweight memory footprint)**:
    - LLM Generation: Qwen2.5 (via Ollama Cloud or OpenAI-compatible hosted provider).
    - Prompt Injection Classifier: ProtectAI DeBERTa v3 Prompt Injection v2 (via Hugging Face Inference API / hosted endpoint).
    - Harmful Content Guard: Meta Llama Guard 3 1B (via hosted API / Ollama Cloud).
  - **Evaluation & Metrics**: Promptfoo, DeepEval, Ragas, Scikit-learn, Pandas, Matplotlib.
  - **Testing**: Pytest.

---

## 4. Document Categories & Threat Model
*(Note: Test datasets/PDFs to be provided by user later; framework is built to accept external data cleanly)*
1. **Company Confidential Data**: Synthetic API keys, passwords, employee PII, internal memos.
2. **Drug-Related Information**: Legitimate medical/side-effect safety vs. harmful misuse instructions.
3. **Weapon-Related Information**: Historical/classification safety vs. operational weaponization content.
4. **Adversarial Injections**: Payloads hidden in documents attempting prompt overrides, system prompt exfiltration, and jailbreaks.

---

## 5. System Architecture
```
[Ingestion Pipeline]
  Raw PDF ──> PyMuPDF ──> Chunking ──> [Security Scanner] ──> [Policy Engine: Allow / Mask / Quarantine]
                                                                        │
                                                                        ▼
                                                       [Embeddings: all-MiniLM-L6-v2]
                                                                        │
                                                                        ▼
                                                            [Qdrant Cloud Collections]
                                                            (baseline vs. secured)

[Query Pipeline (Mode 3)]
  User Query ──> [Query Guard: Injection & Intent]
                     │
                     ▼
                 [Auth & Scope Engine]
                     │
                     ▼
             [Qdrant Retrieval]
                     │
                     ▼
        [Retrieved-Context Scanner & Sanitizer]
                     │
                     ▼
        [Secure Prompt Framing (Untrusted Context)]
                     │
                     ▼
             [LLM Generation: Qwen2.5]
                     │
                     ▼
        [Output Guard: Leakage & Llama Guard]
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
