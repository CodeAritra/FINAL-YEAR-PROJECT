"""
Evaluation Reporting and Chart Generation Module.
Outputs Rich terminal tables and renders publication-ready Matplotlib comparison graphs
differentiating between Hosted (Groq) and Local (Ollama) execution modes.
"""

from pathlib import Path
import logging
from rich.console import Console
from rich.table import Table
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt

from evaluation.evaluator import EvaluationRunReport, AggregatedMetrics

logger = logging.getLogger(__name__)
console = Console()


class EvaluationReporter:
    """Renders tabular comparison reports and research graphs across the 3 evaluation pillars."""

    @staticmethod
    def print_terminal_report(report: EvaluationRunReport) -> None:
        """Display formatted comparison metrics across the 3 research pillars using Rich."""
        console.print(f"\n[bold magenta]═══════════════════════════════════════════════════════════════════════════════════════════[/bold magenta]")
        console.print(f"       [bold white]TRIPARTITE RAG SECURITY & QUALITY EVALUATION REPORT [Run: {report.timestamp}][/bold white]")
        console.print(f"[bold magenta]═══════════════════════════════════════════════════════════════════════════════════════════[/bold magenta]\n")

        # ---------------------------------------------------------
        # Table 1: Security Efficacy Report (Pillar 1)
        # ---------------------------------------------------------
        table_sec = Table(
            title="[bold red]1. Security Efficacy Benchmark (Threat Mitigation)[/bold red]",
            header_style="bold magenta",
        )
        table_sec.add_column("Security Mode", style="cyan", no_wrap=True)
        table_sec.add_column("Exec Mode", style="yellow")
        table_sec.add_column("Main Model", style="dim white")
        table_sec.add_column("ASR (%) ↓", justify="right", style="bold red")
        table_sec.add_column("SILR (%) ↓", justify="right", style="bright_red")
        table_sec.add_column("PISR (%) ↓", justify="right", style="bright_yellow")
        table_sec.add_column("FPR (%) ↓", justify="right", style="yellow")
        table_sec.add_column("Refusal Acc (%) ↑", justify="right", style="bold green")

        for mode_key in report.modes_evaluated:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_key)
            if not m:
                continue
            table_sec.add_row(
                m.mode.upper(),
                m.model_mode.upper(),
                m.model_name[:20],
                f"{m.attack_success_rate:.1f}%",
                f"{m.sensitive_info_leakage_rate:.1f}%",
                f"{m.prompt_injection_success_rate:.1f}%",
                f"{m.false_positive_rate:.1f}%",
                f"{m.refusal_accuracy:.1f}%",
            )

        console.print(table_sec)
        console.print("[dim]  Note: ASR = Attack Success Rate, SILR = Secret Leakage, PISR = Prompt Injection, FPR = False Positives[/dim]\n")

        # ---------------------------------------------------------
        # Table 2: Operational Quality & Groundedness Report (Pillar 2)
        # ---------------------------------------------------------
        table_qual = Table(
            title="[bold green]2. Operational Quality & Groundedness Benchmark (RAG Utility)[/bold green]",
            header_style="bold green",
        )
        table_qual.add_column("Security Mode", style="cyan", no_wrap=True)
        table_qual.add_column("Exec Mode", style="yellow")
        table_qual.add_column("Main Model", style="dim white")
        table_qual.add_column("Safe Acc (%) ↑", justify="right", style="bold green")
        table_qual.add_column("Context Hit Rate ↑", justify="right", style="cyan")
        table_qual.add_column("Faithfulness (%) ↑", justify="right", style="bold cyan")
        table_qual.add_column("Parametric Leak ↓", justify="right", style="bold red")
        table_qual.add_column("Over-Defense (ODR) ↓", justify="right", style="yellow")

        for mode_key in report.modes_evaluated:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_key)
            if not m:
                continue
            table_qual.add_row(
                m.mode.upper(),
                m.model_mode.upper(),
                m.model_name[:20],
                f"{m.safe_answer_accuracy:.1f}%",
                f"{m.context_hit_rate:.1f}%",
                f"{m.avg_faithfulness:.1f}%",
                f"{m.parametric_leakage_rate:.1f}%",
                f"{m.over_defense_rate:.1f}%",
            )

        console.print(table_qual)
        console.print("[dim]  Note: Faithfulness = Claim Grounding in Chunks, Parametric Leak = Answering Out-of-Scope from Weights[/dim]\n")

        # ---------------------------------------------------------
        # Table 3: Performance, Cost & Latency Report (Pillar 3)
        # ---------------------------------------------------------
        table_perf = Table(
            title="[bold blue]3. Performance, Cost & Latency Benchmark (Operational Feasibility)[/bold blue]",
            header_style="bold blue",
        )
        table_perf.add_column("Security Mode", style="cyan", no_wrap=True)
        table_perf.add_column("Exec Mode", style="yellow")
        table_perf.add_column("Retrieval Lat", justify="right", style="cyan")
        table_perf.add_column("Generation Lat", justify="right", style="white")
        table_perf.add_column("Guardrail Overhead", justify="right", style="bold magenta")
        table_perf.add_column("Total Latency", justify="right", style="bold blue")
        table_perf.add_column("Mean Vector Score", justify="right", style="dim white")

        for mode_key in report.modes_evaluated:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_key)
            if not m:
                continue
            table_perf.add_row(
                m.mode.upper(),
                m.model_mode.upper(),
                f"{m.avg_latency_retrieval_ms:.1f} ms",
                f"{m.avg_latency_generation_ms:.1f} ms",
                f"{m.avg_guardrail_overhead_ms:.1f} ms",
                f"{m.avg_latency_total_ms:.1f} ms",
                f"{m.avg_retrieval_score:.4f}",
            )

        console.print(table_perf)
        console.print(f"[dim]Total test samples evaluated: {report.total_test_cases} | Results saved to: {report.jsonl_output_path}[/dim]\n")

    @staticmethod
    def generate_markdown_report(report: EvaluationRunReport, output_path: str | Path | None = None) -> str:
        """Generate a comprehensive Markdown report containing the 3 evaluation tables from the terminal."""
        dest_path = (
            Path(output_path)
            if output_path
            else Path(report.jsonl_output_path).parent / f"eval_run_{report.timestamp}.md"
        )

        lines = [
            f"# Tripartite RAG Security & Quality Evaluation Report",
            f"",
            f"- **Evaluation Run Timestamp**: `{report.timestamp}`",
            f"- **Total Test Samples Evaluated**: `{report.total_test_cases}`",
            f"- **Model Execution Modes**: `{', '.join(report.model_modes_evaluated)}`",
            f"- **Security Modes Evaluated**: `{', '.join(report.modes_evaluated)}`",
            f"",
            f"---",
            f"",
            f"## 1. Security Efficacy Benchmark (Threat Mitigation)",
            f"",
            f"| Security Mode | Exec Mode | Main Model | ASR (%) ↓ | SILR (%) ↓ | PISR (%) ↓ | FPR (%) ↓ | Refusal Acc (%) ↑ |",
            f"| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
        ]

        for mode_key in report.modes_evaluated:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_key)
            if not m:
                continue
            lines.append(
                f"| {m.mode.upper()} | {m.model_mode.upper()} | {m.model_name} | "
                f"{m.attack_success_rate:.1f}% | {m.sensitive_info_leakage_rate:.1f}% | "
                f"{m.prompt_injection_success_rate:.1f}% | {m.false_positive_rate:.1f}% | "
                f"{m.refusal_accuracy:.1f}% |"
            )

        lines.extend([
            "",
            "> **Pillar 1 Metric Definitions**:",
            "> - **ASR (Attack Success Rate)**: Percentage of malicious, harmful, or sensitive requests that bypassed defenses.",
            "> - **SILR (Sensitive Information Leakage Rate)**: Frequency of unauthorized secrets, credentials, or restricted data exposure.",
            "> - **PISR (Prompt Injection Success Rate)**: Rate of jailbreak or system instruction overrides.",
            "> - **FPR (False Positive Rate)**: Percentage of benign questions incorrectly blocked.",
            "> - **Refusal Accuracy**: Proportion of malicious queries properly refused.",
            "",
            "---",
            "",
            "## 2. Operational Quality & Groundedness Benchmark (RAG Utility)",
            "",
            "| Security Mode | Exec Mode | Main Model | Safe Acc (%) ↑ | Context Hit Rate ↑ | Faithfulness (%) ↑ | Parametric Leak ↓ | Over-Defense (ODR) ↓ |",
            "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
        ])

        for mode_key in report.modes_evaluated:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_key)
            if not m:
                continue
            lines.append(
                f"| {m.mode.upper()} | {m.model_mode.upper()} | {m.model_name} | "
                f"{m.safe_answer_accuracy:.1f}% | {m.context_hit_rate:.1f}% | "
                f"{m.avg_faithfulness:.1f}% | {m.parametric_leakage_rate:.1f}% | "
                f"{m.over_defense_rate:.1f}% |"
            )

        lines.extend([
            "",
            "> **Pillar 2 Metric Definitions**:",
            "> - **Safe Accuracy**: Correct answers provided on benign, answerable questions.",
            "> - **Context Hit Rate**: Precision of retrieving ground-truth document chunks from Qdrant.",
            "> - **Faithfulness (Groundedness)**: Token-grounding of generated claims supported by retrieved context.",
            "> - **Parametric Leakage**: Rate of the model hallucinating ungrounded facts from pre-trained weights when context is absent.",
            "> - **Over-Defense Rate (ODR)**: Legitimate queries refused due to false security boundaries.",
            "",
            "---",
            "",
            "## 3. Performance, Cost & Latency Benchmark (Operational Feasibility)",
            "",
            "| Security Mode | Exec Mode | Retrieval Lat | Generation Lat | Guardrail Overhead | Total Latency | Mean Vector Score |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
        ])

        for mode_key in report.modes_evaluated:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_key)
            if not m:
                continue
            lines.append(
                f"| {m.mode.upper()} | {m.model_mode.upper()} | "
                f"{m.avg_latency_retrieval_ms:.1f} ms | {m.avg_latency_generation_ms:.1f} ms | "
                f"{m.avg_guardrail_overhead_ms:.1f} ms | {m.avg_latency_total_ms:.1f} ms | "
                f"{m.avg_retrieval_score:.4f} |"
            )

        lines.extend([
            "",
            "> **Pillar 3 Metric Definitions**:",
            "> - **Retrieval Latency**: Vector embedding and Qdrant retrieval search time.",
            "> - **Generation Latency**: Time spent by the main LLM generating tokens.",
            "> - **Guardrail Overhead**: Security inspection time across query guard, RBAC, context sanitization, and output scanning.",
            "> - **Total Latency**: End-to-end user-perceived turnaround time.",
            "> - **Mean Vector Score**: Average cosine similarity of retrieved context snippets.",
            "",
            "---",
            "",
            "### Generated Run Artifacts",
            "",
            f"- **Detailed Benchmark Records (JSONL)**: `{Path(report.jsonl_output_path).name}`",
            f"- **Tabular Export (CSV)**: `{Path(report.csv_output_path).name}`",
            f"- **Research Comparison Chart (PNG)**: `comparison_chart_{report.timestamp}.png`",
            f"- **Markdown Summary Report (MD)**: `{dest_path.name}`",
            "",
        ])

        dest_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Markdown evaluation report saved to: {dest_path}")
        report.md_output_path = str(dest_path)
        return str(dest_path)

    @staticmethod
    def generate_research_charts(report: EvaluationRunReport, output_path: str | Path | None = None) -> str:
        """Generate 3-panel Matplotlib comparison charts comparing the 3 research pillars."""
        modes = report.modes_evaluated
        if not modes:
            return ""

        metrics_list = [report.metrics_by_mode[m] for m in modes if m in report.metrics_by_mode]
        labels = [f"{m.mode.title()}\n({m.model_mode})" for m in metrics_list]
        x = range(len(labels))

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(max(16, len(labels) * 3.0), 5.5), dpi=300)

        # Plot 1: Security Violations (Lower is Better)
        width = 0.2
        asrs = [m.attack_success_rate for m in metrics_list]
        silrs = [m.sensitive_info_leakage_rate for m in metrics_list]
        pisrs = [m.prompt_injection_success_rate for m in metrics_list]
        fprs = [m.false_positive_rate for m in metrics_list]

        ax1.bar([i - 1.5 * width for i in x], asrs, width=width, label="Attack Success (ASR)", color="#e63946")
        ax1.bar([i - 0.5 * width for i in x], silrs, width=width, label="Info Leakage (SILR)", color="#f4a261")
        ax1.bar([i + 0.5 * width for i in x], pisrs, width=width, label="Prompt Injection (PISR)", color="#e76f51")
        ax1.bar([i + 1.5 * width for i in x], fprs, width=width, label="False Positives (FPR)", color="#2a9d8f")

        ax1.set_title("1. Security Violations (%) [Lower is Better]", fontsize=10, fontweight="bold")
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, fontweight="bold", fontsize=8)
        ax1.set_ylabel("Violation Rate (%)")
        ax1.set_ylim(0, 105)
        ax1.grid(axis="y", linestyle="--", alpha=0.5)
        ax1.legend(loc="upper right", fontsize=7)

        # Plot 2: Operational Quality & Groundedness (Higher is Better)
        w2 = 0.25
        safe_accs = [m.safe_answer_accuracy for m in metrics_list]
        hits = [m.context_hit_rate for m in metrics_list]
        faiths = [m.avg_faithfulness for m in metrics_list]

        ax2.bar([i - w2 for i in x], safe_accs, width=w2, label="Safe Accuracy", color="#2b9348")
        ax2.bar([i for i in x], hits, width=w2, label="Context Hit Rate", color="#0077b6")
        ax2.bar([i + w2 for i in x], faiths, width=w2, label="Faithfulness (Grounded)", color="#55a630")

        ax2.set_title("2. Operational Quality (%) [Higher is Better]", fontsize=10, fontweight="bold")
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, fontweight="bold", fontsize=8)
        ax2.set_ylabel("Quality Score (%)")
        ax2.set_ylim(0, 105)
        ax2.grid(axis="y", linestyle="--", alpha=0.5)
        ax2.legend(loc="upper right", fontsize=7)

        # Plot 3: Latency & Guardrail Overhead Breakdown (ms)
        ret_lats = [m.avg_latency_retrieval_ms for m in metrics_list]
        gen_lats = [m.avg_latency_generation_ms for m in metrics_list]
        overheads = [m.avg_guardrail_overhead_ms for m in metrics_list]

        p1 = ax3.bar(labels, ret_lats, width=0.45, label="Retrieval (Qdrant)", color="#457b9d")
        p2 = ax3.bar(labels, gen_lats, width=0.45, bottom=ret_lats, label="Generation (LLM)", color="#1d3557")
        bottom_sum = [ret_lats[i] + gen_lats[i] for i in range(len(labels))]
        p3 = ax3.bar(labels, overheads, width=0.45, bottom=bottom_sum, label="Guardrail Overhead", color="#e76f51")

        ax3.set_title("3. Latency Breakdown (ms)", fontsize=10, fontweight="bold")
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels, fontweight="bold", fontsize=8)
        ax3.set_ylabel("Latency (ms)")
        ax3.grid(axis="y", linestyle="--", alpha=0.5)
        ax3.legend(loc="upper left", fontsize=7)

        for i, m in enumerate(metrics_list):
            total_h = m.avg_latency_total_ms
            ax3.annotate(
                f"{total_h:.0f} ms",
                xy=(i, total_h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=8,
            )

        plt.tight_layout()

        dest_path = (
            Path(output_path)
            if output_path
            else Path(report.jsonl_output_path).parent / f"comparison_chart_{report.timestamp}.png"
        )
        fig.savefig(dest_path)
        plt.close(fig)

        logger.info(f"Tripartite research comparison chart saved to: {dest_path}")
        return str(dest_path)
