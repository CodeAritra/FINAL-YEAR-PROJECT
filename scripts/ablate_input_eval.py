"""
Ablation Experiment Runner: Disables the Input Guardrail (Query Guard + RBAC).
Runs evaluation to demonstrate downstream Defense-in-Depth (Context Sanitization + Output Guard).

Usage:
  python scripts/ablate_input_eval.py 20
  python scripts/ablate_input_eval.py 50
  python scripts/ablate_input_eval.py 20 --model-mode local
"""

import sys
import subprocess
from pathlib import Path

def main():
    sample_size = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("20", "50", "100") else "20"
    dataset_file = Path(f"evaluation/datasets/balanced_{sample_size}_benchmark.json")

    if not dataset_file.exists():
        print(f"Generating balanced benchmark for {sample_size} questions...")
        from scripts.build_balanced_benchmarks import create_benchmarks
        create_benchmarks()

    extra_args = [arg for arg in sys.argv[1:] if arg not in ("20", "50", "100")]

    cmd = [
        sys.executable,
        "main.py",
        "evaluate",
        "--dataset",
        str(dataset_file),
        "--ablate",
        "input",
        *extra_args,
    ]

    print("\n" + "="*80)
    print(">> RUNNING ABLATION EXPERIMENT: INPUT GUARD DISABLED (Query Guard + RBAC Off)")
    print(">> Demonstrating downstream interception: Context Delimiters & Output Secret Scanner")
    print(f">> Executing: {' '.join(cmd)}")
    print("="*80 + "\n")

    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
