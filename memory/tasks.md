# Task Roadmap & Backlog

> **Current Milestone**: Milestone 3 — Ingest PDFs & Execute Automated Benchmarks
> **Last Updated**: 2026-11-07

---

## High-Priority / Current Sprint

| ID | Task | Role | Priority | Status | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TASK-005` | Prepare Research PDFs | User / Developer | P0 | `Completed` | `documents/forensics.pdf` and `documents/company internal doc.pdf` added to workspace |
| `TASK-006` | Construct Evaluation Benchmark Datasets | QA / Curator | P0 | `Completed` | Created 25 structured test cases across `evaluation/datasets/` |
| `TASK-007` | Ingest PDFs into Qdrant Collections | Developer | P0 | `Ready to Run` | Execute `python main.py ingest --folder documents/` |
| `TASK-008` | Run Automated Evaluation Across 3 Modes | QA Engineer | P0 | `Ready to Run` | Execute `python main.py evaluate --dataset evaluation/datasets/full_evaluation_benchmark.json --all` |
| `TASK-009` | Generate Comparative Publication Charts | Curator | P1 | `Pending TASK-008` | Execute `python main.py report` to produce ASR, SILR, PISR, and latency graphs |

---

## Evaluation Benchmark Datasets Ready

- [`evaluation/datasets/forensics_benchmark.json`](evaluation/datasets/forensics_benchmark.json): 20 adversarial forensic operational queries.
- [`evaluation/datasets/company_confidential_benchmark.json`](evaluation/datasets/company_confidential_benchmark.json): 5 corporate secret extraction & permission tier queries.
- [`evaluation/datasets/full_evaluation_benchmark.json`](evaluation/datasets/full_evaluation_benchmark.json): Combined 25-sample benchmark suite.
