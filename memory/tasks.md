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
| `TASK-021` | Streamline Tripartite Metrics & Visual Labels | Architect / QA | P0 | `Completed` | Folded SILR into ASR, removed PISR, renamed Safe Acc -> Benign QA Acc, renamed PLR -> Hallucination Rate, eliminated duplicate ODR (same as FPR), added model & execution mode to research charts |
| `TASK-022` | Defense-in-Depth Stage Breakdown Table & 4-Panel Charts | Architect / Developer | P0 | `Completed` | Added Table 4 (Stage-Wise Breakdown: Input, Retrieval, Context, Output, Clean Pass) to terminal & Markdown, and upgraded research charts to a 4-panel 2x2 publication figure |
| `TASK-023` | Diversified Multi-Stage Benchmark & Telemetry | QA / Developer | P0 | `Completed` | Created `diversified_20_benchmark.json`, builder script, `run_eval.py diversified` runner, and `scripts/showcase_multistage_defense.py` demonstrating distributed stage interception across Input, Context, and Output layers |
| `TASK-024` | Metric Normalization, Redaction Recognition & Table 4 Summation | Architect / QA | P0 | `Completed` | Fixed Table 4 summation to 100% by using total_blocked denominator, streamlined Table 4 to active stages (Input & Context), added unicode typography normalization, fixed redaction-as-defense recognition, and eliminated false hallucination counts |
| `TASK-025` | Remove Benign QA Acc, Refusal Acc Fix & Parameterless Redis Secret Redaction | Architect / QA | P0 | `Completed` | Removed Benign QA Acc from terminal, Markdown, and Subplot 2; corrected Refusal Accuracy to require affirmative refusal strings; updated Database Connection URI regex for parameterless Redis strings; regenerated 122358 report & charts |
| `TASK-026` | Standalone Markdown-to-Chart Generator & Demo MD | Developer / Curator | P0 | `Completed` | Implemented `scripts/render_charts_from_md.py` and `python main.py chart <file.md>` rendering 4 individual charts + 1 combined 2x2 figure from any benchmark Markdown file; created `demo_tables.md` |
| `TASK-027` | Comprehensive Master Landing Guide (landing.md) | Documentation Curator | P0 | `Completed` | Authored `landing.md` detailing architecture tree, metric formulas, viva Q&A defense rationale, tools breakdown, and CLI instructions in simple, pointwise language |
| `TASK-028` | PDF Export of Research Master Guides (learning.pdf & methodology.pdf) | Documentation Curator | P1 | `Completed` | Generalized `scripts/convert_to_pdf.py` producing publication-grade `learning.pdf` and `methodology.pdf` with running headers, footers, math typesetting, and balanced page layout |

---

## Evaluation Benchmark Datasets Ready

- [`evaluation/datasets/company_100_benchmark.json`](evaluation/datasets/company_100_benchmark.json): 100 corporate questions (50 Answerable, 50 Refusal).
- [`evaluation/datasets/forensics_100_benchmark.json`](evaluation/datasets/forensics_100_benchmark.json): 100 forensic questions (50 Answerable, 50 Refusal).
- [`evaluation/datasets/full_200_benchmark.json`](evaluation/datasets/full_200_benchmark.json) / [`full_evaluation_benchmark.json`](evaluation/datasets/full_evaluation_benchmark.json): Complete 200-question unified benchmark suite (100 Answerable, 100 Refusal - exact 50/50 balance).
