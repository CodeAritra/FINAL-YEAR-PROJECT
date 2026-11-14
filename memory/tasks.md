# Task Roadmap & Backlog

> **Current Milestone**: Milestone 3 — Ingest PDFs & Execute Automated Benchmarks
> **Last Updated**: 2026-11-07

---

## High-Priority / Current Sprint

| ID | Task | Role | Priority | Status | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TASK-005` | Prepare Research PDFs | User / Developer | P0 | `Completed` | `documents/forensics.pdf` and `documents/company internal doc.pdf` added to workspace |
| `TASK-006` | Construct Evaluation Benchmark Datasets | QA / Curator | P0 | `Completed` | Created initial 25 structured test cases across `evaluation/datasets/` |
| `TASK-007` | Ingest PDFs into Qdrant Collections | Developer | P0 | `Completed` | Ingested 86 chunks across baseline and secured Qdrant Cloud collections |
| `TASK-008` | Run Automated Evaluation Across 3 Modes | QA Engineer | P0 | `Completed` | Executed 75-sample multi-mode benchmark via `python main.py evaluate` |
| `TASK-009` | Generate Comparative Publication Charts | Curator | P1 | `Completed` | Generated `comparison_chart_20261108_081734.png` in `storage/eval_results/` |
| `TASK-010` | Database Cleanup & Reset Utility | Developer | P1 | `Completed` | Implemented `scripts/clean_qdrant.py` and `python main.py clean` command |
| `TASK-011` | Document Inspection & Sanitization Exporter | Developer | P1 | `Completed` | Built `ingestion/inspector.py` and `python main.py inspect` to export sanitized `.txt` files |
| `TASK-012` | Live Progress Reporting & Refusal Regex Fix | Developer | P1 | `Completed` | Fixed conversational refusal matching and added per-sample live console progress |
| `TASK-013` | Expand Dataset to 200 Questions (100/PDF) | QA Engineer | P0 | `Completed` | Ingested all 200 questions: 100 Company (50 ans / 50 refuse) + 100 Forensics (50 ans / 50 refuse); strict 50/50 balance |
| `TASK-014` | Integrate User-Provided 100/100 Benchmark | QA Engineer | P0 | `Completed` | Integrated full 200 questions across `forensics_100_benchmark.json`, `company_100_benchmark.json`, and `full_200_benchmark.json` |
| `TASK-015` | Tripartite Evaluation Architecture (3 Reports) | Architect / QA | P0 | `Completed` | Implemented 3 distinct reports (Security Efficacy, Operational Quality, Latency/Cost) & 3-panel research charts |
| `TASK-016` | Research Methodology Documentation | Architect / Lead | P0 | `Completed` | Authored publication-grade `methodology.md` covering Threat Model, $2 \times 3$ Factorial Design, 6-stage Guardrail Architecture |
| `TASK-017` | Proactive Rate-Pacing Throttler for Groq TPM | Developer | P1 | `Completed` | Added automatic dynamic inter-request pacing (10.0s for 8K TPM models, 1.5s for 8B models, `--pacing` CLI flag) to eliminate 429 lockouts |
| `TASK-018` | 50-Sample Balanced Tripartite Evaluation | QA Engineer | P0 | `Completed` | Evaluated 150 total queries across 3 modes with 100% attack mitigation (0% ASR), 0% parametric leakage, and 50% faster total latency |
| `TASK-019` | Markdown Evaluation Report Exporter (.md) | Developer / Curator | P1 | `Completed` | Implemented `generate_markdown_report` export matching all 3 terminal tables (`eval_run_<timestamp>.md`) |
| `TASK-020` | Balanced Non-Skewed Multi-Doc Benchmarks & Runner | QA / Developer | P0 | `Completed` | Created `balanced_100_benchmark.json`, `balanced_50_benchmark.json`, `balanced_20_benchmark.json`, builder script, and `run_eval.py` runner |

---

## Evaluation Benchmark Datasets Ready

- [`evaluation/datasets/company_100_benchmark.json`](evaluation/datasets/company_100_benchmark.json): 100 corporate questions (50 Answerable, 50 Refusal).
- [`evaluation/datasets/forensics_100_benchmark.json`](evaluation/datasets/forensics_100_benchmark.json): 100 forensic questions (50 Answerable, 50 Refusal).
- [`evaluation/datasets/full_200_benchmark.json`](evaluation/datasets/full_200_benchmark.json) / [`full_evaluation_benchmark.json`](evaluation/datasets/full_evaluation_benchmark.json): Complete 200-question unified benchmark suite (100 Answerable, 100 Refusal - exact 50/50 balance).
