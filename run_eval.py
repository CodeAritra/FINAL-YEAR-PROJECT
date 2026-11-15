"""
Unified Benchmark Evaluation Runner.
Executes perfectly balanced, non-skewed, multi-stage diversified benchmarks
across all 3 security modes (Baseline, Prompt-Only, Guardrail).

Usage:
  python run_eval.py         (Defaults to the full 200-question diversified benchmark)
  python run_eval.py 200     (Full 200-question diversified benchmark)
  python run_eval.py 100     (100-question diversified benchmark)
  python run_eval.py 50      (50-question diversified benchmark)
  python run_eval.py 20      (20-question rapid diversified benchmark)

Auto-Detection:
  Automatically detects whether to run in HOSTED mode (Groq API: gpt-oss-120b)
  or LOCAL mode (Ollama: llama3.2) based on your .env configuration and API availability.
  No separate scripts or manual mode flags required!
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import settings

def auto_detect_model_mode() -> str:
    """
    Automatically detects whether to use hosted (Groq) or local (Ollama) mode.
    Prioritizes .env MODEL_MODE or presence of a valid GROQ_API_KEY.
    """
    env_mode = (os.getenv("MODEL_MODE") or settings.model_mode or "").lower().strip()
    groq_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key

    if env_mode == "local":
        return "local"
    if groq_key and len(groq_key) > 10 and not groq_key.startswith("your_"):
        return "hosted"
    return "local"

def main():
    # Supported sample sizes
    valid_sizes = {"20", "50", "100", "200"}

    # Default to 200 if no size provided, or parse size from first argument
    if len(sys.argv) == 1:
        size = "200"
        extra_args = []
    elif sys.argv[1] in valid_sizes:
        size = sys.argv[1]
        extra_args = sys.argv[2:]
    elif sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)
    else:
        print(f"Unknown argument '{sys.argv[1]}'. Valid sizes: 20, 50, 100, 200")
        print("Usage:")
        print("  python run_eval.py         (Runs 200 diversified questions)")
        print("  python run_eval.py 20      (Runs 20 diversified questions)")
        print("  python run_eval.py 50      (Runs 50 diversified questions)")
        print("  python run_eval.py 100     (Runs 100 diversified questions)")
        print("  python run_eval.py 200     (Runs 200 diversified questions)")
        sys.exit(1)

    # Resolve dataset path
    dataset_file = BASE_DIR / "evaluation" / "datasets" / f"diversified_{size}_benchmark.json"

    # Automatically generate dataset if missing
    if not dataset_file.exists():
        print(f"[*] Benchmark dataset '{dataset_file.name}' not found. Generating diversified benchmark suite now...")
        from scripts.build_diversified_benchmarks import build_all_diversified_benchmarks
        build_all_diversified_benchmarks()

    # Automatically detect model execution mode (hosted vs local)
    detected_mode = auto_detect_model_mode()

    # Check if user explicitly passed --model-mode in extra_args; if not, pass auto-detected mode
    has_model_mode_flag = any(arg in ("--model-mode", "-M") for arg in extra_args)
    mode_args = [] if has_model_mode_flag else ["--model-mode", detected_mode]

    mode_display = "HOSTED (Groq API: gpt-oss-120b)" if detected_mode == "hosted" else "LOCAL (Ollama: llama3.2)"
    
    print("=" * 78)
    print(f"[*] Multi-Layer RAG Evaluation: {size} Diversified Test Cases")
    print(f"[*] Target Benchmark: {dataset_file.name}")
    print(f"[*] Distribution: 50% Benign QA + 50% Threats [Input (40%) | Context (30%) | Output (30%)]")
    print(f"[*] Auto-Detected Execution Mode: {mode_display}")
    print("=" * 78 + "\n")

    cmd = [
        sys.executable,
        "main.py",
        "evaluate",
        "--dataset",
        str(dataset_file),
        *mode_args,
        *extra_args,
    ]

    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
