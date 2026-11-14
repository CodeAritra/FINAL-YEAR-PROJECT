# Methodology: Multi-Layer Security Guardrail Framework for RAG Systems

## 1. Threat Modeling & Adversarial Assumptions

Retrieval-Augmented Generation (RAG) combines dense semantic retrieval with parametric Large Language Model (LLM) generation. While RAG grounds model generation in external reference knowledge, it simultaneously expands the system's attack surface. In this research, we evaluate three primary threat vectors:

```
                                  ┌───────────────────────────┐
                                  │      ATTACK VECTORS       │
                                  └─────────────┬─────────────┘
                ┌───────────────────────────────┼───────────────────────────────┐
                ▼                               ▼                               ▼
    ┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
    │ 1. Confidentiality    │       │ 2. Integrity & Control│       │ 3. Safety & Harm      │
    │    Leakage (SILR)     │       │    Hijacking (PISR)   │       │    Generation (ASR)   │
    │ AWS Keys, URIs, PII   │       │ Indirect Injections,  │       │ Operational weapon /  │
    │ in internal documents │       │ System prompt bypass  │       │ exploit generation    │
    └───────────────────────┘       └───────────────────────┘       └───────────────────────┘
```

1. **Confidential Information & Credential Leakage**:
   - *Threat*: Internal documents often contain hardcoded infrastructure secrets (AWS credentials, database connection strings, bearer tokens) and Personally Identifiable Information (PII). An untrusted or low-clearance user can prompt the system to exfiltrate these strings.
2. **Indirect & Direct Prompt Injection**:
   - *Threat*: Adversarial strings embedded inside third-party PDFs or user queries that instruct the LLM to ignore system instructions, alter its persona (e.g., "Do Anything Now" / DAN), or leak internal framing prompts.
3. **Harmful Operational Content Generation**:
   - *Threat*: Technical or sensitive domain manuals (e.g., forensic handbooks, biomedical protocols) can be exploited to generate actionable physical harm instructions, weapon synthesis guides, or evidence destruction blueprints.

### Adversarial Assumptions
- The adversary has black-box access to the RAG endpoint.
- The adversary may submit adversarial queries directly or have partial access to documents indexed in the vector database (indirect prompt injection).
- The vector database stores heterogeneous documents containing both public and restricted clearance tiers.

---

## 2. Experimental Design & Tri-Mode Comparison

To rigorously isolate the efficacy of external guardrails versus prompt-level defenses, the framework defines a **$2 \times 3$ Factorial Research Matrix** decoupling the **Model Execution Mode** from the **Research Security Mode**.

```
┌─────────────────────────────────┬────────────────────────────────────────────────────────┐
│                                 │                  Model Execution Mode                  │
│                                 ├────────────────────────────┬───────────────────────────┤
│                                 │     Hosted Cloud Mode      │      Local LLM Mode       │
│                                 │    (Groq GPT-OSS-120B)     │      (Ollama Llama-3.2)   │
├──────────────┬──────────────────┼────────────────────────────┼───────────────────────────┤
│              │ Mode 1: Baseline │ Exp 1: Baseline-Hosted     │ Exp 4: Baseline-Local     │
│   Research   ├──────────────────┼────────────────────────────┼───────────────────────────┤
│   Security   │ Mode 2: Prompt-  │ Exp 2: PromptOnly-Hosted   │ Exp 5: PromptOnly-Local   │
│     Mode     │         Only     │                            │                           │
│              ├──────────────────┼────────────────────────────┼───────────────────────────┤
│              │ Mode 3: Multi-   │ Exp 3: Guardrail-Hosted    │ Exp 6: Guardrail-Local    │
│              │         Layer    │                            │                           │
└──────────────┴──────────────────┴────────────────────────────┴───────────────────────────┘
```

### Research Security Modes
1. **Mode 1 — Baseline RAG (Control Group)**:
   - Uses standard document parsing, dense retrieval, and unconstrained LLM generation.
   - Operates with **zero** guardrails, filters, or security checks.
   - Evaluates the raw vulnerability of standard commercial RAG pipelines.
2. **Mode 2 — Prompt-Only Defensive RAG (Heuristic Defense)**:
   - Retains the exact retrieval pipeline of Baseline RAG.
   - Implements security solely through a defensive system prompt instructing the LLM to refuse confidential disclosures and ignore adversarial overrides.
   - Uses **zero** programmatic classifiers, regex scanners, or access control engines.
3. **Mode 3 — Multi-Layer Guardrail RAG (Proposed Framework)**:
   - Implements a deterministic, six-stage defense-in-depth architecture spanning ingestion, query validation, access control, context isolation, LLM generation, and output scanning.

### Model Execution Modes
1. **Hosted Cloud Mode**:
   - Main LLM: `openai/gpt-oss-120b` executed via Groq API (LPUs).
   - Embeddings: `gemini-embedding-2` (768 dimensions) via Google GenAI SDK.
   - Prompt Injection Guard: `meta-llama/llama-prompt-guard-2-86m` via Groq API.
2. **Local LLM Mode**:
   - Main LLM: `llama3.2:1b` executed locally via Ollama daemon (`http://localhost:11434/v1`).
   - Hardware Target: Standard consumer laptop with $\le 8\text{ GB}$ RAM.
   - Prompt Injection Guard & Embeddings: Shared cloud API endpoints to maintain consistent classification accuracy without exceeding local RAM limits.

---

## 3. Data Ingestion & Dual Indexing Pipeline

To eliminate data leakage between modes, document ingestion is split into two isolated branches feeding dedicated Qdrant collections.

```
Research PDFs (documents/)
       │
       ▼
Text Extraction (PyMuPDF / fitz v1.25.3)
       │
       ▼
Document Inspector (storage/processed_docs/*.txt)
       │
       ▼
Recursive Chunking (LangChain: 500 chars, 50 overlap)
       │
       ├───────────────────────────────────────────────┐
       ▼                                               ▼
[Branch A: Baseline Ingestion]                 [Branch B: Secured Ingestion]
Raw, Unsanitized Chunks                        Policy Engine Ingestion Inspection
       │                                         ├─ Secret Redaction (Regex + Entropy H ≥ 4.5)
       │                                         ├─ PII Masking (Presidio + spaCy)
       │                                         └─ Injection Quarantine (Prompt Guard 2 86M)
       ▼                                               ▼
Dense Vectorization                            Dense Vectorization
(Gemini Embedding 2, 768d)                     (Gemini Embedding 2, 768d)
       │                                               │
       ▼                                               ▼
Qdrant Cloud: baseline_rag                     Qdrant Cloud: secured_rag
```

### Ingestion Steps
1. **Extraction**: `PyMuPDF` (`fitz`) parses raw text, structural headings, page numbers, and document metadata from uploaded PDFs.
2. **Inspection & Pre-Chunking Export**: `DocumentInspector` exports full-text sanitization audits to `storage/processed_docs/` for human verification.
3. **Recursive Chunking**: `RecursiveCharacterTextSplitter` segments text into 500-character chunks with a 50-character sliding window overlap across paragraph boundaries (`["\n\n", "\n", " ", ""]`).
4. **Branch A (Baseline)**: Chunks are converted to dense vectors without sanitization and indexed into the `baseline_rag` Qdrant collection.
5. **Branch B (Secured)**: Chunks pass through the Multi-Layer Ingestion Firewall before vectorization:
   - **Secret Redaction**: Credentials matching high-entropy regex patterns are replaced with `[REDACTED_SECRET: <TYPE>]`.
   - **PII Anonymization**: Entity recognition masks sensitive personal data with synthetic entity identifiers (e.g., `<EMAIL_ADDRESS>`).
   - **Adversarial Quarantine**: Chunks exhibiting prompt injection patterns classified by Llama Prompt Guard 2 86M are dropped from indexing.
6. **Vector Indexing**: Both collections use **Cosine Similarity** on 768-dimensional dense vectors generated by `gemini-embedding-2`.

---

## 4. Multi-Layer Guardrail Architecture (The 6-Stage Defense)

The proposed security architecture defends against attacks across six discrete checkpoints:

```
[User Query + User Role Clearance]
                │
                ▼
┌────────────────────────────────────────────────────────┐
│ Layer 2: Query Security Firewall                       │
│ Model: Meta Llama Prompt Guard 2 86M (Groq API)        │
│ Decision: ALLOW or BLOCK (Jailbreak / System Override) │
└──────────────────────────┬─────────────────────────────┘
                           │ (Clean Query)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Layer 3: Role-Based Access Control (RBAC) Engine       │
│ Clearances: ANONYMOUS (0), RESEARCHER (1),             │
│             STAFF (2), ADMIN (3)                       │
│ Rule: Filter out chunks exceeding clearance tier       │
└──────────────────────────┬─────────────────────────────┘
                           │ (Authorized Request)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Layer 4: Context Retrieval & Sanitization              │
│ 1. Vector Search: Qdrant Top-K (K=4, secured_rag)      │
│ 2. Sanitizer: Strip prompt injection trigger prefixes  │
│ 3. Enclosure: Wrap in <retrieved_untrusted_data> XML   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Layer 5: Secure LLM Generation Router                  │
│ Hosted: Groq GPT-OSS-120B | Local: Ollama Llama-3.2:1B │
│ Framing: Rigid isolation instructions                  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Layer 6: Output Security Scanning & Redaction          │
│ Engine: Regex Secret Detector + Canary Token Check     │
│ Action: Intercept / redact surviving leaked keys       │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
                 [Verified Safe Answer]
```

### Stage Specifications
* **Layer 1 (Ingestion Security)**: Neutralizes threat vectors at rest before persistent storage.
* **Layer 2 (Query Security Firewall)**: Evaluates user input using Meta Llama Prompt Guard 2 86M hosted via Groq Cloud API ($\sim 25\text{ ms}$ latency). If adversarial intent probability $>0.5$, execution aborts with a `[GUARDRAIL BLOCK]` response.
* **Layer 3 (Access Control & Clearance Scoping)**: Enforces Role-Based Access Control (RBAC) matching user clearance against document sensitivity metadata:
  $$\text{Clearance}(\text{User}) \ge \text{Sensitivity}(\text{Document})$$
  Chunks violating clearance constraints are purged from retrieval candidates.
* **Layer 4 (Retrieved-Context Sanitization)**: Retrieved chunks are treated as untrusted data. The context sanitizer strips prefix attack templates (e.g., `"Ignore previous instructions"`, `"System alert:"`) and encloses snippets within `<retrieved_untrusted_data>` delimiters.
* **Layer 5 (Secure LLM Generation)**: The generation prompt strictly decouples the system instructions from the passive retrieved text, preventing the LLM from executing commands inside context tags.
* **Layer 6 (Output Security Scanning)**: Final generated tokens are scanned prior to delivery. Any surviving secrets or accidental credential echoes are intercepted and replaced with redacted placeholders.

---

## 5. Benchmark Dataset Design & Corpus

The framework is evaluated using two dedicated research documents reflecting realistic enterprise and operational threats:

1. **`forensics.pdf` (Operational Harm Testbed)**:
   - *Nature*: Forensic death investigation and physical evidence suppression manual.
   - *Evaluation Scope*: Evaluates whether the system refuses actionable instructions on lethal harm, evidence tampering, and toxicological procedures.
2. **`company internal doc.pdf` (Confidentiality Testbed)**:
   - *Nature*: Internal operational documentation for Northwind Analytics.
   - *Evaluation Scope*: Contains synthetic yet valid credential-shaped secrets (AWS access keys, PostgreSQL connection URIs with passwords, Stripe webhook secrets) and employee PII.

### Balanced Sampling Protocol
Evaluation datasets are balanced $50/50$ across two behavioral expectations:
* **Answerable Test Cases ($50\%$)**: Benign, factual questions intended to measure answer accuracy, context hit rate, and groundedness.
* **Unanswerable / Refusal Test Cases ($50\%$)**: Adversarial prompts, secret extraction probes, and operational harm queries intended to test refusal accuracy.

```
                      ┌─────────────────────────────────────────┐
                      │    BENCHMARK DATASET SUITE (N Cases)    │
                      └────────────────────┬────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
        ┌───────────────────────┐                     ┌───────────────────────┐
        │  Answerable (50%)     │                     │  Unanswerable (50%)   │
        │  Expected: ANSWER     │                     │  Expected: REFUSE     │
        ├───────────────────────┤                     ├───────────────────────┤
        │ • Normal Questions    │                     │ • Harmful Requests    │
        │ • Safe Domain Facts   │                     │ • Secret Extraction   │
        │                       │                     │ • Prompt Injection    │
        └───────────────────────┘                     └───────────────────────┘
```

---

## 6. The Tripartite Evaluation Paradigm

Evaluating a RAG security framework solely on threat mitigation creates an **over-defense bias**: a system that refuses $100\%$ of user queries achieves $0\%$ Attack Success Rate, yet possesses zero operational utility. 

To overcome this limitation, this research establishes the **Tripartite Evaluation Paradigm**, simultaneously measuring performance across three distinct pillars:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   THE TRIPARTITE RAG EVALUATION PARADIGM                         │
├──────────────────────────┬───────────────────────────┬───────────────────────────┤
│    Pillar 1: Security    │   Pillar 2: Operational   │      Pillar 3: Cost &     │
│         Efficacy         │   Quality & Faithfulness  │     Latency Overhead      │
│   (Threat Mitigation)    │       (RAG Utility)       │  (Operational Feasibility)│
└──────────────────────────┴───────────────────────────┴───────────────────────────┘
```

### Pillar 1: Security Efficacy Metrics (Threat Mitigation)
1. **Attack Success Rate (ASR) [$\downarrow$ Lower is Better]**:
   $$\text{ASR} = \frac{\sum \mathbb{I}(\text{Harmful or Adversarial Request Executed})}{\text{Total Threat Requests Tested}} \times 100$$
2. **Sensitive Information Leakage Rate (SILR) [$\downarrow$ Lower is Better]**:
   $$\text{SILR} = \frac{\sum \mathbb{I}(\text{Target Secret or Credential Leaked})}{\text{Total Secret Extraction Probes}} \times 100$$
3. **Prompt Injection Success Rate (PISR) [$\downarrow$ Lower is Better]**:
   $$\text{PISR} = \frac{\sum \mathbb{I}(\text{System Instruction or Persona Overridden})}{\text{Total Prompt Injection Attacks}} \times 100$$
4. **False Positive Rate (FPR) [$\downarrow$ Lower is Better]**:
   $$\text{FPR} = \frac{\sum \mathbb{I}(\text{Safe, Legitimate Query Improperly Refused})}{\text{Total Safe Queries Tested}} \times 100$$
5. **Refusal Accuracy [$\uparrow$ Higher is Better]**:
   $$\text{Refusal Accuracy} = \frac{\sum \mathbb{I}(\text{Adversarial Query Correctly Refused})}{\text{Total Adversarial Queries Tested}} \times 100$$

### Pillar 2: Operational Quality & Groundedness Metrics (RAG Utility)
1. **Safe Answer Accuracy [$\uparrow$ Higher is Better]**:
   $$\text{Safe Acc} = \frac{\sum \mathbb{I}(\text{Safe Query Answered Correctly with Required Facts})}{\text{Total Safe Queries Tested}} \times 100$$
2. **Context Hit Rate (Hit@4) [$\uparrow$ Higher is Better]**:
   $$\text{Hit@4} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(\text{Relevant Ground-Truth Snippet} \in \text{Top-4 Retrieved Chunks})$$
3. **Context Faithfulness / Groundedness Score [$\uparrow$ Higher is Better]**:
   Measures the token-level groundedness of non-refusal model answers against retrieved context:
   $$\text{Faithfulness} = \frac{|\text{Content Tokens in Answer Grounded in Retrieved Chunks}|}{|\text{Total Content Tokens in Answer}|} \times 100$$
4. **Parametric Leakage Rate [$\downarrow$ Lower is Better]**:
   Quantifies how often the LLM answers out-of-scope or unanswerable queries using pre-trained parametric weights instead of bounding answers to provided documents.
5. **Over-Defense Rate (ODR) [$\downarrow$ Lower is Better]**:
   Measures the frequency of legitimate inquiries blocked due to over-sensitive guardrail classification ($\text{ODR} \equiv \text{FPR}$).

### Pillar 3: Performance, Cost & Latency Overhead (Operational Feasibility)
1. **Retrieval Latency ($\text{Latency}_{\text{Retrieval}}$)**: Time consumed by Gemini Embedding 2 generation and Qdrant Cloud cosine similarity search.
2. **Generation Latency ($\text{Latency}_{\text{Generation}}$)**: Time consumed by LLM token generation (Groq GPT-OSS-120B or local Ollama).
3. **Guardrail Overhead Latency ($\text{Latency}_{\text{Guardrail}}$)**:
   $$\text{Latency}_{\text{Guardrail}} = \text{Latency}_{\text{Total}} - (\text{Latency}_{\text{Retrieval}} + \text{Latency}_{\text{Generation}})$$
   Isolates the millisecond cost added by the multi-layer inspection stack.
4. **Mean Vector Cosine Score**: Average cosine similarity score of retrieved snippets, quantifying retrieval confidence.

---

## 7. Ablation Study Methodology

To evaluate the individual contributions of each security layer, the framework implements an **Ablation Engine** allowing selective deactivation of specific security stages:

```
┌────────────────────────────────────────────────────────┐
│               ABLATION EXPERIMENT SUITE                │
├────────────────────┬───────────────────────────────────┤
│ Ablation Run       │ Deactivated Layer                 │
├────────────────────┼───────────────────────────────────┤
│ Ablate-Ingestion   │ Disables Secret & PII Redaction   │
│ Ablate-Query       │ Disables Llama Prompt Guard 2 86M │
│ Ablate-Context     │ Disables Delimiter Containment    │
│ Ablate-Output      │ Disables Output Secret Scanner    │
└────────────────────┴───────────────────────────────────┘
```

By executing identical benchmark test cases against each ablated configuration, the framework measures:
1. The **marginal increase in ASR/SILR** when a specific layer is removed.
2. The **latency reduction** achieved by removing that layer.
3. The empirical proof of **Defense-in-Depth**: demonstrating that if an adversary bypasses Layer 2 (Query Guard), downstream layers (Context Sanitization and Output Scanning) successfully intercept the attack.

