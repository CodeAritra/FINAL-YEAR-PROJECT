"""
Benchmark Dataset Builder and Validator.
Provides utilities to import, validate, merge, and inspect evaluation benchmark datasets.
"""

import sys
from pathlib import Path
import json
import re
from typing import Optional, List, Dict, Any

# Ensure parent directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import typer
from rich.console import Console
from rich.table import Table

from evaluation.test_case import (
    EvaluationTestCase,
    EvaluationCategory,
    ExpectedBehavior,
    DatasetLoader,
)

app = typer.Typer(
    help="Benchmark Dataset Builder and Validator for RAG Security Evaluation.",
    add_completion=False,
)
console = Console()

DATASETS_DIR = Path("evaluation/datasets")


def validate_test_cases(cases: List[EvaluationTestCase]) -> Dict[str, Any]:
    """Analyze and return statistics about a list of test cases."""
    ans_count = sum(1 for c in cases if c.expected_behavior == ExpectedBehavior.ANSWER)
    refuse_count = sum(1 for c in cases if c.expected_behavior == ExpectedBehavior.REFUSE)
    redact_count = sum(1 for c in cases if c.expected_behavior == ExpectedBehavior.REDACT)

    cat_counts: Dict[str, int] = {}
    for c in cases:
        val = c.category.value if hasattr(c.category, "value") else str(c.category)
        cat_counts[val] = cat_counts.get(val, 0) + 1

    unique_ids = set()
    duplicate_ids = []
    for c in cases:
        if c.test_id in unique_ids:
            duplicate_ids.append(c.test_id)
        unique_ids.add(c.test_id)

    return {
        "total": len(cases),
        "answerable": ans_count,
        "refuse": refuse_count,
        "redact": redact_count,
        "unanswerable": refuse_count + redact_count,
        "categories": cat_counts,
        "duplicate_ids": duplicate_ids,
    }


@app.command()
def stats(
    directory: Path = typer.Option(
        DATASETS_DIR,
        "--dir",
        "-d",
        help="Directory containing benchmark dataset JSON files.",
    )
):
    """Scan and display statistics for all benchmark datasets in the folder."""
    if not directory.exists():
        console.print(f"[bold red]Directory '{directory}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    json_files = sorted(list(directory.glob("*.json")))
    if not json_files:
        console.print(f"[yellow]No .json benchmark files found in '{directory}'.[/yellow]")
        return

    table = Table(title="Benchmark Datasets Summary", header_style="bold magenta")
    table.add_column("Dataset File", style="cyan")
    table.add_column("Total", justify="right", style="bold white")
    table.add_column("Answerable", justify="right", style="bold green")
    table.add_column("Unanswerable", justify="right", style="bold red")
    table.add_column("Balance", justify="center", style="yellow")
    table.add_column("Categories Breakdown", style="dim")

    for jf in json_files:
        try:
            cases = DatasetLoader.load_from_file(jf)
            info = validate_test_cases(cases)
            tot = info["total"]
            ans = info["answerable"]
            unans = info["unanswerable"]

            balance_str = f"{ans}/{unans}"
            if tot > 0:
                pct = (ans / tot) * 100
                balance_str += f" ({pct:.0f}%)"

            cat_str = ", ".join(f"{k}: {v}" for k, v in sorted(info["categories"].items()))
            table.add_row(
                jf.name,
                str(tot),
                str(ans),
                str(unans),
                balance_str,
                cat_str,
            )
        except Exception as e:
            table.add_row(jf.name, "ERR", "-", "-", "-", f"Failed to parse: {e}")

    console.print(table)


@app.command()
def validate(
    path: Path = typer.Option(
        ...,
        "--path",
        "-p",
        help="Path to dataset JSON/JSONL file to validate.",
    )
):
    """Validate schema compliance and integrity of a specific benchmark dataset file."""
    if not path.exists():
        console.print(f"[bold red]File '{path}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"\n[bold cyan]Validating Dataset:[/bold cyan] [underline]{path}[/underline]")
    try:
        cases = DatasetLoader.load_from_file(path)
        info = validate_test_cases(cases)

        console.print(f"  • [bold white]Total Test Cases:[/bold white] {info['total']}")
        console.print(f"  • [bold green]Answerable (Expected Answer):[/bold green] {info['answerable']}")
        console.print(f"  • [bold red]Unanswerable (Expected Refusal/Redaction):[/bold red] {info['unanswerable']}")

        if info["duplicate_ids"]:
            console.print(f"  • [bold red]Duplicate IDs Detected:[/bold red] {info['duplicate_ids']}")
        else:
            console.print(f"  • [green]All Test IDs are unique.[/green]")

        console.print("\n[bold]Category Breakdown:[/bold]")
        for cat, cnt in sorted(info["categories"].items()):
            console.print(f"  - {cat:25s}: {cnt}")

        console.print(f"\n[bold green][OK] Dataset is schema-compliant and valid.[/bold green]\n")
    except Exception as e:
        console.print(f"[bold red]Validation failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def merge(
    forensics_file: Path = typer.Option(
        DATASETS_DIR / "forensics_100_benchmark.json",
        "--forensics",
        "-f",
        help="Forensics benchmark file path.",
    ),
    company_file: Path = typer.Option(
        DATASETS_DIR / "company_100_benchmark.json",
        "--company",
        "-c",
        help="Company confidential benchmark file path.",
    ),
    output_file: Path = typer.Option(
        DATASETS_DIR / "full_200_benchmark.json",
        "--output",
        "-o",
        help="Output path for merged 200-question benchmark file.",
    ),
    update_full_benchmark: bool = typer.Option(
        True,
        "--update-full-benchmark",
        help="Also overwrite evaluation/datasets/full_evaluation_benchmark.json with the merged list.",
    ),
):
    """Merge Forensics and Company Confidential datasets into a unified benchmark."""
    # Fallback to existing benchmarks if 100-question ones are not yet created
    if not forensics_file.exists():
        fallback = DATASETS_DIR / "forensics_benchmark.json"
        if fallback.exists():
            console.print(f"[yellow]Notice: '{forensics_file.name}' not found. Using fallback '{fallback.name}'.[/yellow]")
            forensics_file = fallback
    if not company_file.exists():
        fallback = DATASETS_DIR / "company_confidential_benchmark.json"
        if fallback.exists():
            console.print(f"[yellow]Notice: '{company_file.name}' not found. Using fallback '{fallback.name}'.[/yellow]")
            company_file = fallback

    if not forensics_file.exists() or not company_file.exists():
        console.print(f"[bold red]Error: Input files missing. Check paths.[/bold red]")
        raise typer.Exit(code=1)

    f_cases = DatasetLoader.load_from_file(forensics_file)
    c_cases = DatasetLoader.load_from_file(company_file)

    merged = f_cases + c_cases
    console.print(f"\n[cyan]Merging {len(f_cases)} ({forensics_file.name}) + {len(c_cases)} ({company_file.name}) = {len(merged)} test cases.[/cyan]")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as out_f:
        json.dump([c.model_dump() for c in merged], out_f, indent=2)
    console.print(f"[bold green][OK] Saved merged benchmark to:[/bold green] [underline]{output_file}[/underline]")

    if update_full_benchmark:
        std_full = DATASETS_DIR / "full_evaluation_benchmark.json"
        with open(std_full, "w", encoding="utf-8") as s_f:
            json.dump([c.model_dump() for c in merged], s_f, indent=2)
        console.print(f"[bold green][OK] Also synchronized:[/bold green] [underline]{std_full}[/underline]\n")


def parse_and_create_test_case(
    test_id: str,
    query: str,
    category: str,
    expected_behavior: str,
    source_doc: str,
    target_secrets: Optional[List[str]] = None,
    forbidden_tokens: Optional[List[str]] = None,
    required_keywords: Optional[List[str]] = None,
    user_role: str = "RESEARCHER",
    target_sensitivity: str = "INTERNAL",
    metadata: Optional[Dict[str, Any]] = None,
) -> EvaluationTestCase:
    """Helper factory to instantiate an EvaluationTestCase."""
    return EvaluationTestCase(
        test_id=test_id,
        category=EvaluationCategory(category),
        query=query.strip(),
        expected_behavior=ExpectedBehavior(expected_behavior),
        target_secrets=target_secrets or [],
        forbidden_tokens=forbidden_tokens or [],
        required_keywords=required_keywords or [],
        user_role=user_role,
        target_sensitivity=target_sensitivity,
        metadata={"source_doc": source_doc, **(metadata or {})},
    )


if __name__ == "__main__":
    app()
