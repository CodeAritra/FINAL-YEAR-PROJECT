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
| `TASK-013` | Expand Dataset to 200 Questions (100/PDF) | QA Engineer | P1 | `In Progress` | Built `scripts/build_dataset.py` & evaluation sampling flags (`--target`, `--sample 10/50/all`); awaiting user question list |
| `TASK-014` | Integrate User-Provided 100/100 Benchmark | QA Engineer | P0 | `Ready / Pending Input` | Ingest user questions into `forensics_100_benchmark.json`, `company_100_benchmark.json`, and `full_200_benchmark.json` |
| `TASK-015` | Tripartite Evaluation Architecture (3 Reports) | Architect / QA | P0 | `Completed` | Implemented 3 distinct reports (Security Efficacy, Operational Quality, Latency/Cost) & 3-panel research charts |

---

## Evaluation Benchmark Datasets Ready

- [`evaluation/datasets/forensics_benchmark.json`](evaluation/datasets/forensics_benchmark.json): 20 adversarial forensic operational queries.
- [`evaluation/datasets/company_confidential_benchmark.json`](evaluation/datasets/company_confidential_benchmark.json): 5 corporate secret extraction & permission tier queries.
- [`evaluation/datasets/full_evaluation_benchmark.json`](evaluation/datasets/full_evaluation_benchmark.json): Combined 25-sample benchmark suite.
