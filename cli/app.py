"""
CLI Application Module using Typer and Rich.
Provides user-facing commands for document ingestion, multi-mode querying,
automated evaluation benchmarking, and research reporting.
Supports:
- Two Model Execution Modes: Hosted (Groq GPT-OSS-120B) vs. Local (Ollama)
- Three Research Security Modes: Baseline, Prompt-Only, and Multi-Layer Guardrail
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

from config.settings import settings
from config.model_config import ModelExecutionMode, ResearchSecurityMode
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
from providers.ollama_provider import OllamaProvider

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
def inspect(
    folder: Path = typer.Option(
        Path("documents"),
        "--folder",
        "-f",
        help="Directory containing PDF documents to extract and inspect.",
    ),
    output_dir: Path = typer.Option(
        Path("storage/processed_docs"),
        "--output-dir",
        "-o",
        help="Directory where sanitized .txt files will be saved.",
    ),
):
    """Extract raw PDF text, apply security guardrails (Secrets + PII), and export sanitized .txt files."""
    from ingestion.inspector import DocumentInspector

    console.print(f"\n[bold cyan][*] Inspecting and Sanitizing Documents[/bold cyan] from [yellow]{folder}[/yellow]")
    if not folder.exists():
        console.print(f"[bold red]Error: Folder or file '{folder}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    try:
        inspector = DocumentInspector()
        results = inspector.inspect_and_export(folder, output_dir=output_dir)

        if not results:
            console.print("[yellow]No PDF documents found to inspect.[/yellow]\n")
            return

        table = Table(title="Document Inspection & Sanitization Summary", header_style="bold green")
        table.add_column("PDF Document", style="cyan")
        table.add_column("Pages", style="white", justify="right")
        table.add_column("Raw Chars", style="dim", justify="right")
        table.add_column("Secrets Redacted", style="bold red", justify="right")
        table.add_column("PII Masked", style="bold yellow", justify="right")
        table.add_column("Exported File", style="green")

        for r in results:
            sec_desc = f"{r.secrets_count}" + (f" ({', '.join(r.secrets_types)})" if r.secrets_types else "")
            pii_desc = f"{r.pii_count}" + (f" ({', '.join(r.pii_types)})" if r.pii_types else "")
            rel_path = Path(r.output_txt_path).name
            table.add_row(
                r.filename,
                str(r.total_pages),
                f"{r.raw_characters:,}",
                sec_desc,
                pii_desc,
                f"{output_dir.name}/{rel_path}",
            )

        console.print(table)
        console.print(
            f"\n[bold green][OK] Processed {len(results)} document(s). Saved sanitized text to:[/bold green] [underline]{output_dir}[/underline]\n"
        )

    except Exception as e:
        console.print(f"[bold red]Inspection failed:[/bold red] {e}")
        raise typer.Exit(code=1)



@app.command()
def ask(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="The question to ask."),
    mode: str = typer.Option(
        "guardrail",
        "--mode",
        "-m",
        "--security-mode",
        help="Research security mode: 'baseline', 'prompt-only', or 'guardrail'.",
    ),
    model_mode: Optional[str] = typer.Option(
        None,
        "--model-mode",
        "-M",
        help="Model execution mode: 'hosted' (Groq GPT-OSS-120B) or 'local' (Ollama).",
    ),
    role: str = typer.Option(
        "RESEARCHER",
        "--role",
        "-r",
        help="User role clearance: 'ANONYMOUS', 'RESEARCHER', 'STAFF', or 'ADMIN'.",
    ),
    top_k: int = typer.Option(4, "--top-k", "-k", help="Number of retrieved snippets."),
):
    """Query the RAG system under a chosen security mode and model execution mode."""
    if not query:
        query = typer.prompt("Enter your question")

    active_model_mode = (model_mode or settings.model_mode).lower().strip()
    sec_mode = mode.lower().strip()

    # Validate setup
    is_valid, warnings = settings.validate_setup(active_model_mode)
    if not is_valid:
        console.print("\n[bold yellow][!] Configuration Notice:[/bold yellow]")
        for w in warnings:
            console.print(f"  • {w}")
        console.print("[dim]Using fallback simulation where credentials are empty.[/dim]\n")

    console.print(f"\n[bold cyan][*] Query Execution:[/bold cyan]")
    console.print(f"  • [bold white]Security Mode:[/bold white] [bold yellow]{sec_mode.upper()}[/bold yellow]")
    console.print(f"  • [bold white]Model Execution Mode:[/bold white] [bold green]{active_model_mode.upper()}[/bold green]")
    console.print(f"  • [bold white]User Role:[/bold white] {role} | [bold white]Top-K:[/bold white] {top_k}\n")

    try:
        if sec_mode == "baseline":
            system = BaselineRAG()
            result = system.run(query=query, top_k=top_k, model_mode=active_model_mode)
        elif sec_mode in ("prompt-only", "prompt_only"):
            system = PromptOnlyRAG()
            result = system.run(query=query, top_k=top_k, model_mode=active_model_mode)
        elif sec_mode in ("guardrail", "secured"):
            system = GuardrailRAG()
            user_role = UserRole(role.upper())
            result = system.run(query=query, user_role=user_role, top_k=top_k, model_mode=active_model_mode)
        else:
            console.print(f"[bold red]Unknown security mode '{mode}'. Choose 'baseline', 'prompt-only', or 'guardrail'.[/bold red]")
            raise typer.Exit(code=1)

        # Output Response
        console.print(Panel(result.response, title=f"Generated Answer [{result.mode} | {result.model_mode} - {result.model_name}]", border_style="green"))

        # Latency breakdown
        lat_table = Table(title="Latency Breakdown (ms)", header_style="bold blue")
        lat_table.add_column("Stage", style="cyan")
        lat_table.add_column("Latency (ms)", justify="right", style="white")
        lat_table.add_row("Retrieval (Gemini Embedding 2)", f"{result.latency_retrieval_ms:.2f}")
        lat_table.add_row("Generation", f"{result.latency_generation_ms:.2f}")
        lat_table.add_row("Total Pipeline", f"{result.latency_total_ms:.2f}")
        console.print(lat_table)

    except Exception as e:
        console.print(f"[bold red]Query execution error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def evaluate(
    target: str = typer.Option(
        "all",
        "--target",
        "-t",
        help="Target document dataset: 'forensics', 'company', or 'all'.",
    ),
    sample: str = typer.Option(
        "all",
        "--sample",
        "-s",
        help="Sample size: '10' (5 answerable, 5 unanswerable), '50' (25 answerable, 25 unanswerable), or 'all'.",
    ),
    dataset: Optional[Path] = typer.Option(
        None,
        "--dataset",
        "-d",
        help="Custom path to evaluation dataset (.json or .jsonl). Overrides --target.",
    ),
    all_modes: bool = typer.Option(
        True,
        "--all",
        help="Run evaluation across all three security modes (baseline, prompt-only, guardrail).",
    ),
    model_mode: str = typer.Option(
        "hosted",
        "--model-mode",
        "-M",
        help="Model execution mode: 'hosted', 'local', or 'all' (evaluates both hosted & local).",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-n",
        help="Limit evaluation to first N test cases.",
    ),
    ablate_layer: Optional[str] = typer.Option(
        None,
        "--ablate",
        help="Disable specific guardrail layer for ablation: 'ingestion', 'query', 'context', 'output'.",
    ),
):
    """Run automated benchmark evaluation across security modes with customizable sampling and target dataset."""
    console.print("\n[bold magenta][*] Multi-Layer RAG Security Evaluation Runner[/bold magenta]\n")

    # 1. Resolve dataset path based on --target or explicit --dataset
    datasets_dir = Path("evaluation/datasets")
    if dataset:
        target_path = dataset
    elif target.lower() == "forensics":
        f100 = datasets_dir / "forensics_100_benchmark.json"
        target_path = f100 if f100.exists() else datasets_dir / "forensics_benchmark.json"
    elif target.lower() in ("company", "company_doc", "company_internal"):
        c100 = datasets_dir / "company_100_benchmark.json"
        target_path = c100 if c100.exists() else datasets_dir / "company_confidential_benchmark.json"
    else:  # "all"
        full200 = datasets_dir / "full_200_benchmark.json"
        target_path = full200 if full200.exists() else datasets_dir / "full_evaluation_benchmark.json"

    if not target_path.exists():
        console.print(f"[bold red]Error: Dataset file not found at '{target_path}'.[/bold red]")
        raise typer.Exit(code=1)

    all_cases = DatasetLoader.load_from_file(target_path)
    console.print(f"[cyan]Loaded total {len(all_cases)} test cases from {target_path.name}.[/cyan]")

    # 2. Balanced Sampling (50% answerable, 50% unanswerable)
    from evaluation.test_case import ExpectedBehavior
    ans_cases = [tc for tc in all_cases if tc.expected_behavior == ExpectedBehavior.ANSWER]
    unans_cases = [tc for tc in all_cases if tc.expected_behavior != ExpectedBehavior.ANSWER]

    sample_val = sample.lower().strip()
    if sample_val in ("10", "50"):
        target_half = 5 if sample_val == "10" else 25
        ans_sample = ans_cases[:target_half]
        unans_sample = unans_cases[:target_half]
        test_cases = ans_sample + unans_sample
        console.print(
            f"[green]Sampled {len(test_cases)} questions: "
            f"{len(ans_sample)} Answerable + {len(unans_sample)} Unanswerable "
            f"(target requested: {sample_val}).[/green]"
        )
        if len(ans_sample) < target_half:
            console.print(
                f"[yellow][!] Dataset '{target_path.name}' currently contains {len(ans_cases)} answerable question(s). "
                f"Full 50/50 balance ({target_half}/{target_half}) will be active once the expanded benchmark is loaded.[/yellow]"
            )
    elif limit and limit > 0:
        test_cases = all_cases[:limit]
        console.print(f"[green]Limited to first {len(test_cases)} test cases.[/green]")
    else:
        test_cases = all_cases
        console.print(f"[green]Evaluating all {len(test_cases)} questions ({len(ans_cases)} Answerable, {len(unans_cases)} Unanswerable).[/green]")

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
    report = runner.run_all(test_cases, model_mode=model_mode, ablation_policy=ablation_policy)

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

    records = []
    with open(target_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                import json
                records.append(json.loads(line))

    console.print(f"Total evaluated samples: {len(records)}")
    modes = list(set(r.get("mode") for r in records))
    model_modes = list(set(r.get("model_mode") for r in records))
    console.print(f"Security modes: {', '.join(modes)}")
    console.print(f"Model execution modes: {', '.join(model_modes)}")


@app.command()
def status():
    """Check connectivity and operational health of Qdrant Cloud and model providers."""
    console.print("\n[bold cyan][*] System Status & Diagnostics[/bold cyan]\n")

    table = Table(title="Environment & Component Health", header_style="bold blue")
    table.add_column("Component", style="cyan")
    table.add_column("Configuration", style="white")
    table.add_column("Status", style="bold green")

    # Qdrant Check
    try:
        qm = QdrantManager()
        base_info = qm.get_collection_info(settings.qdrant_collection_baseline)
        table.add_row("Vector DB (Qdrant)", settings.qdrant_url, f"Connected ({base_info['status']})")
    except Exception as e:
        table.add_row("Vector DB (Qdrant)", settings.qdrant_url, f"[red]Disconnected ({e})[/red]")

    # Gemini Embedding 2 Check
    gemini_key_status = "[green]Configured[/green]" if settings.gemini_api_key else "[yellow]Missing GEMINI_API_KEY[/yellow]"
    table.add_row("Embedding Model", f"{settings.gemini_embedding_model} (dim: {settings.gemini_embedding_dimension})", gemini_key_status)

    # Groq Main LLM Check
    groq_key_status = "[green]Configured[/green]" if settings.groq_api_key else "[yellow]Missing GROQ_API_KEY[/yellow]"
    table.add_row("Hosted Main LLM", f"Groq {settings.groq_model}", groq_key_status)

    # Groq Llama Prompt Guard 2 Check
    table.add_row("Prompt Guard (Groq)", settings.groq_prompt_guard_model, groq_key_status)

    # Local Ollama Check
    ollama = OllamaProvider()
    if ollama.is_alive():
        local_models = ollama.list_local_models()
        models_str = ", ".join(local_models[:3]) if local_models else "no models pulled yet"
        table.add_row("Local LLM (Ollama)", f"{settings.ollama_model} ({settings.ollama_base_url})", f"[green]Running[/green] ({models_str})")
    else:
        table.add_row("Local LLM (Ollama)", f"{settings.ollama_model} ({settings.ollama_base_url})", "[yellow]Offline (start with 'ollama serve')[/yellow]")

    # Application Mode
    table.add_row("Default Execution Mode", settings.model_mode.upper(), "Active")
    table.add_row("Presidio PII Engine", f"Enabled ({settings.presidio_language})", "Ready")
    table.add_row("Secret Regex Detector", "10 Default Patterns + Entropy", "Ready")

    console.print(table)
    console.print()


@app.command()
def clean(
    target: str = typer.Option(
        "both",
        "--target",
        "-t",
        help="Target collections to clean: 'baseline', 'secured', 'both', or 'all'.",
    ),
    recreate: bool = typer.Option(
        True,
        "--recreate/--no-recreate",
        "-r/-nr",
        help="Whether to immediately recreate empty collections with proper dimensions after purge.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        "-y",
        help="Skip interactive confirmation prompt.",
    ),
):
    """Purge and reset vector collections in Qdrant (baseline_rag, secured_rag, or all)."""
    from scripts.clean_qdrant import clean_qdrant as execute_clean

    if target == "all":
        execute_clean(clean_all=True, recreate=recreate, force=force)
    elif target == "baseline":
        execute_clean(collections=[settings.qdrant_collection_baseline], recreate=recreate, force=force)
    elif target == "secured":
        execute_clean(collections=[settings.qdrant_collection_secured], recreate=recreate, force=force)
    else:  # "both"
        execute_clean(
            collections=[settings.qdrant_collection_baseline, settings.qdrant_collection_secured],
            recreate=recreate,
            force=force,
        )

