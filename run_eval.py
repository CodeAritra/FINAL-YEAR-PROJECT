"""
Convenient runner script to execute balanced 20, 50, or 100 question evaluations.

Usage:
  python run_eval.py 20
  python run_eval.py 50
  python run_eval.py 100
  python run_eval.py 20 --model-mode local
"""

import sys
import subprocess
from pathlib import Path

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("20", "50", "100"):
        print("Usage:")
        print("  python run_eval.py 20    (Runs the balanced 20-question benchmark)")
        print("  python run_eval.py 50    (Runs the balanced 50-question benchmark)")
        print("  python run_eval.py 100   (Runs the balanced 100-question benchmark)")
        sys.exit(1)

    size = sys.argv[1]
    dataset_file = Path(f"evaluation/datasets/balanced_{size}_benchmark.json")

    if not dataset_file.exists():
        print(f"Dataset file not found at '{dataset_file}'. Generating it now...")
        from scripts.build_balanced_benchmarks import create_benchmarks
        create_benchmarks()

    # Pass through additional flags (e.g. --model-mode local)
    extra_args = sys.argv[2:]

    cmd = [
        sys.executable,
        "main.py",
        "evaluate",
        "--dataset",
        str(dataset_file),
        *extra_args,
    ]

    print(f"\n[*] Executing {size}-question balanced evaluation across all 3 security modes...")
    print(f"[*] Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()

