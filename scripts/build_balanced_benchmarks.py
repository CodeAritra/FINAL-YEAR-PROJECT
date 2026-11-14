"""
Script to generate perfectly balanced, non-skewed 50-question and 100-question benchmarks.

Splits:
100 Questions:
  - 25 Normal from PDF 1 (Forensics)
  - 25 Harmful from PDF 1 (Forensics)
  - 25 Normal from PDF 2 (Company)
  - 25 Restricted from PDF 2 (10 Secret Extractions + 15 Confidential HR/PII)

50 Questions:
  - 13 Normal from PDF 1 (Forensics)
  - 12 Harmful from PDF 1 (Forensics)
  - 12 Normal from PDF 2 (Company)
  - 13 Restricted from PDF 2 (8 Secret Extractions + 5 Confidential HR/PII)
"""

import json
from pathlib import Path

def create_benchmarks():
    base_dir = Path("evaluation/datasets")
    forensics_file = base_dir / "forensics_100_benchmark.json"
    company_file = base_dir / "company_100_benchmark.json"

    with open(forensics_file, "r", encoding="utf-8") as f:
        forensics = json.load(f)
    with open(company_file, "r", encoding="utf-8") as f:
        company = json.load(f)

    # Segregate buckets
    f_ans = [q for q in forensics if q.get("expected_behavior") == "answer"]
    f_harm = [q for q in forensics if q.get("expected_behavior") == "refuse"]

    c_ans = [q for q in company if q.get("expected_behavior") == "answer"]
    c_sec = [q for q in company if q.get("category") == "secret_extraction"]
    c_sens = [q for q in company if q.get("category") == "safe_sensitive_question"]

    # 1. Build 100-Question Dataset (25 each)
    p1_normal_100 = f_ans[:25]
    p1_harmful_100 = f_harm[:25]
    p2_normal_100 = c_ans[:25]
    p2_restricted_100 = c_sec[:10] + c_sens[:15]  # All 10 secrets + 15 sensitive

    benchmark_100 = p1_normal_100 + p1_harmful_100 + p2_normal_100 + p2_restricted_100

    out_100 = base_dir / "balanced_100_benchmark.json"
    with open(out_100, "w", encoding="utf-8") as f:
        json.dump(benchmark_100, f, indent=2)
    print(f"[*] Generated: {out_100} with {len(benchmark_100)} questions.")
    print(f"    - PDF 1 (Forensics): {len(p1_normal_100)} Normal + {len(p1_harmful_100)} Harmful")
    print(f"    - PDF 2 (Company): {len(p2_normal_100)} Normal + {len(p2_restricted_100)} Restricted ({len(c_sec[:10])} Secrets, {len(c_sens[:15])} Sensitive)")

    # 2. Build 50-Question Dataset (Balanced 25 Answer / 25 Refuse)
    p1_normal_50 = f_ans[:13]
    p1_harmful_50 = f_harm[:12]
    p2_normal_50 = c_ans[:12]
    p2_restricted_50 = c_sec[:8] + c_sens[:5]  # 8 secrets + 5 sensitive = 13

    benchmark_50 = p1_normal_50 + p1_harmful_50 + p2_normal_50 + p2_restricted_50

    out_50 = base_dir / "balanced_50_benchmark.json"
    with open(out_50, "w", encoding="utf-8") as f:
        json.dump(benchmark_50, f, indent=2)
    print(f"[*] Generated: {out_50} with {len(benchmark_50)} questions.")
    print(f"    - PDF 1 (Forensics): {len(p1_normal_50)} Normal + {len(p1_harmful_50)} Harmful")
    print(f"    - PDF 2 (Company): {len(p2_normal_50)} Normal + {len(p2_restricted_50)} Restricted ({len(c_sec[:8])} Secrets, {len(c_sens[:5])} Sensitive)")

    # 3. Build 20-Question Dataset (Balanced 10 Answer / 10 Refuse)
    p1_normal_20 = f_ans[:5]
    p1_harmful_20 = f_harm[:5]
    p2_normal_20 = c_ans[:5]
    p2_restricted_20 = c_sec[:3] + c_sens[:2]  # 3 secrets + 2 sensitive = 5

    benchmark_20 = p1_normal_20 + p1_harmful_20 + p2_normal_20 + p2_restricted_20

    out_20 = base_dir / "balanced_20_benchmark.json"
    with open(out_20, "w", encoding="utf-8") as f:
        json.dump(benchmark_20, f, indent=2)
    print(f"[*] Generated: {out_20} with {len(benchmark_20)} questions.")
    print(f"    - PDF 1 (Forensics): {len(p1_normal_20)} Normal + {len(p1_harmful_20)} Harmful")
    print(f"    - PDF 2 (Company): {len(p2_normal_20)} Normal + {len(p2_restricted_20)} Restricted ({len(c_sec[:3])} Secrets, {len(c_sens[:2])} Sensitive)")

if __name__ == "__main__":
    create_benchmarks()

