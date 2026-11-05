"""
CLI Application Module using Typer and Rich.
Provides user-facing commands for document ingestion, multi-mode querying,
automated evaluation benchmarking, and research reporting.
"""

from pathlib import Path
from typing import Optional
import sys
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import settings
from ingestion.pipeline import IngestionPipeline
from modes.baseline import BaselineRAG
from modes.prompt_only import PromptOnlyRAG
from modes.guardrail import GuardrailRAG
from guardrails.access_control import UserRole, DataSensitivity
from evaluation.test_case import DatasetLoader, EvaluationTestCase
from evaluation.evaluator import EvaluationRunner
from evaluation.reporting import EvaluationReporter
from database.qdrant_manager import QdrantManager
from policies.engine import PolicyEngine

app = typer.Typer(
    name="RAG Security Framework",
    help="Multi-Layer Security Framework for RAG Systems (Research Platform)",
    add_completion=False,
)
console = Console()


@app.command()
def ingest(
    folder: Path = typer.Option(
        Path("documents"),
        "--folder",
        "-f",
        help="Directory containing PDF documents to ingest.",
    ),
    target: str = typer.Option(
        "both",
        "--target",
        "-t",
        help="Target collection: 'baseline', 'secured', or 'both'.",
    ),
):
    """Ingest PDF documents, evaluate ingestion security, embed and index into Qdrant."""
    console.print(f"\n[bold cyan][*] Starting Ingestion Pipeline[/bold cyan] from [yellow]{folder}[/yellow]")
    if not folder.exists():
        console.print(f"[bold red]Error: Folder '{folder}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    try:
        pipeline = IngestionPipeline()
        stats = pipeline.ingest_folder(folder, target=target)

        table = Table(title="Ingestion Summary", header_style="bold green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold white", justify="right")

        table.add_row("PDF Files Processed", str(stats.files_processed))
        table.add_row("Total Text Chunks", str(stats.total_chunks))
        table.add_row("Baseline Indexed", str(stats.baseline_indexed))
        table.add_row("Secured Indexed", str(stats.secured_indexed))
        table.add_row("Secrets Redacted", str(stats.secrets_redacted))
        table.add_row("PII Entities Masked", str(stats.pii_masked))
        table.add_row("Injections Quarantined", str(stats.injections_quarantined))

        console.print(table)
        console.print("[bold green][OK] Ingestion completed successfully.[/bold green]\n")

    except Exception as e:
        console.print(f"[bold red]Ingestion failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def ask(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="The question to ask."),
    mode: str = typer.Option(
        "guardrail",
        "--mode",
        "-m",
        help="RAG execution mode: 'baseline', 'prompt-only', or 'guardrail'.",
    ),
    role: str = typer.Option(
        "RESEARCHER",
        "--role",
        "-r",
        help="User role clearance: 'ANONYMOUS', 'RESEARCHER', 'STAFF', or 'ADMIN'.",
    ),
    top_k: int = typer.Option(4, "--top-k", "-k", help="Number of retrieved snippets."),
):
    """Query the RAG system under baseline, prompt-only, or multi-layer guardrail mode."""
    if not query:
        query = typer.prompt("Enter your question")

    mode_normalized = mode.lower().strip()
    console.print(f"\n[bold cyan][*] Executing Query in Mode:[/bold cyan] [bold yellow]{mode_normalized.upper()}[/bold yellow]")
    console.print(f"[dim]User Role: {role} | Top-K: {top_k}[/dim]\n")

    try:
        if mode_normalized == "baseline":
            system = BaselineRAG()
            result = system.run(query=query, top_k=top_k)
        elif mode_normalized in ("prompt-only", "prompt_only"):
            system = PromptOnlyRAG()
            result = system.run(query=query, top_k=top_k)
        elif mode_normalized in ("guardrail", "secured"):
            system = GuardrailRAG()
            user_role = UserRole(role.upper())
            result = system.run(query=query, user_role=user_role, top_k=top_k)
        else:
            console.print(f"[bold red]Unknown mode '{mode}'. Choose 'baseline', 'prompt-only', or 'guardrail'.[/bold red]")
            raise typer.Exit(code=1)

        # Output Response
        console.print(Panel(result.response, title=f"Generated Answer [{result.mode}]", border_style="green"))

        # Latency breakdown
        lat_table = Table(title="Latency Breakdown (ms)", header_style="bold blue")
        lat_table.add_column("Stage", style="cyan")
        lat_table.add_column("Latency (ms)", justify="right", style="white")
        lat_table.add_row("Retrieval", f"{result.latency_retrieval_ms:.2f}")
        lat_table.add_row("Generation", f"{result.latency_generation_ms:.2f}")
        lat_table.add_row("Total Pipeline", f"{result.latency_total_ms:.2f}")
        console.print(lat_table)

    except Exception as e:
        console.print(f"[bold red]Query execution error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def evaluate(
    dataset: Path = typer.Option(
        None,
        "--dataset",
        "-d",
        help="Path to evaluation dataset (.json or .jsonl).",
    ),
    all_modes: bool = typer.Option(
        True,
        "--all",
        help="Run evaluation across all three modes (baseline, prompt-only, guardrail).",
    ),
    ablate_layer: Optional[str] = typer.Option(
        None,
        "--ablate",
        help="Disable specific guardrail layer for ablation: 'ingestion', 'query', 'context', 'output'.",
    ),
):
    """Run automated benchmark evaluation across all three RAG systems."""
    console.print("\n[bold magenta][*] Multi-Layer RAG Security Evaluation Runner[/bold magenta]\n")

    if dataset is None or not dataset.exists():
        console.print(
            f"[yellow]Notice: No external evaluation dataset passed or file not found at '{dataset}'.\n"
            "The framework is initialized and waiting for your evaluation dataset.\n"
            "Use `--dataset path/to/eval_dataset.json` once you provide the dataset files.[/yellow]"
        )
        raise typer.Exit(code=0)

    test_cases = DatasetLoader.load_from_file(dataset)
    console.print(f"[green]Loaded {len(test_cases)} evaluation test cases from {dataset}.[/green]")

    # Configure ablation if requested
    ablation_policy = None
    if ablate_layer:
        console.print(f"[yellow][!] Ablation experiment active: Disabling layer '{ablate_layer}'.[/yellow]")
        ablation_policy = PolicyEngine(
            enable_ingestion_security=ablate_layer != "ingestion",
            enable_query_security=ablate_layer != "query",
            enable_context_sanitization=ablate_layer != "context",
            enable_output_security=ablate_layer != "output",
        )

    runner = EvaluationRunner()
    report = runner.run_all(test_cases, ablation_policy=ablation_policy)

    # Display Rich table
    EvaluationReporter.print_terminal_report(report)

    # Generate research charts
    chart_path = EvaluationReporter.generate_research_charts(report)
    console.print(f"[bold green][OK] Research comparison chart generated:[/bold green] [underline]{chart_path}[/underline]\n")


@app.command()
def report(
    results_file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Specific evaluation .jsonl file to inspect."
    ),
):
    """Display results and research graphs from recent evaluation runs."""
    eval_dir = settings.storage_dir / "eval_results"
    if not eval_dir.exists():
        console.print(f"[yellow]No evaluation results directory found at {eval_dir}. Run 'python main.py evaluate' first.[/yellow]")
        return

    jsonl_files = sorted(eval_dir.glob("*.jsonl"), reverse=True)
    if not jsonl_files:
        console.print(f"[yellow]No evaluation runs recorded in {eval_dir} yet.[/yellow]")
        return

    target_file = results_file or jsonl_files[0]
    console.print(f"\n[bold cyan][*] Inspecting Evaluation Run:[/bold cyan] [yellow]{target_file.name}[/yellow]")

    # Read records and summarize
    records = []
    with open(target_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                import json
                records.append(json.loads(line))

    console.print(f"Total evaluated samples: {len(records)}")
    modes = list(set(r.get("mode") for r in records))
    console.print(f"Evaluated modes: {', '.join(modes)}")


@app.command()
def status():
    """Check connectivity and operational health of Qdrant Cloud and model interfaces."""
    console.print("\n[bold cyan][*] System Status & Diagnostics[/bold cyan]\n")

    table = Table(title="Environment & Component Health", header_style="bold blue")
    table.add_column("Component", style="cyan")
    table.add_column("Setting / Provider", style="white")
    table.add_column("Status", style="bold green")

    # Qdrant Check
    try:
        qm = QdrantManager()
        base_info = qm.get_collection_info(settings.qdrant_collection_baseline)
        table.add_row("Vector DB (Qdrant)", settings.qdrant_url, f"Connected ({base_info['status']})")
    except Exception as e:
        table.add_row("Vector DB (Qdrant)", settings.qdrant_url, f"[red]Disconnected ({e})[/red]")

    table.add_row("Embeddings", f"{settings.embedding_model_name} ({settings.device})", "Ready")
    table.add_row("LLM Inference", f"{settings.llm_provider} ({settings.llm_model})", "Configured")
    table.add_row("Prompt Injection Guard", f"{settings.prompt_injection_provider}", "Configured")
    table.add_row("Harm Classifier", f"{settings.llama_guard_provider}", "Configured")
    table.add_row("Presidio PII Engine", f"Enabled ({settings.presidio_language})", "Ready")
    table.add_row("Secret Regex Detector", "10 Default Patterns + Entropy", "Ready")

    console.print(table)
    console.print()

