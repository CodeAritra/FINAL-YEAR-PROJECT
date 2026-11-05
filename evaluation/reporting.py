"""
Evaluation Reporting and Chart Generation Module.
Outputs Rich terminal tables and renders publication-ready Matplotlib comparison graphs
for research analysis and publication.
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
    """Renders tabular comparison reports and research graphs."""

    @staticmethod
    def print_terminal_report(report: EvaluationRunReport) -> None:
        """Display formatted comparison metrics in the terminal using Rich."""
        table = Table(
            title=f"🔬 Security Evaluation Benchmark Results [Run: {report.timestamp}]",
            header_style="bold magenta",
        )

        table.add_column("System Mode", style="cyan", no_wrap=True)
        table.add_column("ASR (%)", justify="right", style="red")
        table.add_column("SILR (%)", justify="right", style="bright_red")
        table.add_column("PISR (%)", justify="right", style="bright_yellow")
        table.add_column("FPR (%)", justify="right", style="yellow")
        table.add_column("Safe Acc (%)", justify="right", style="green")
        table.add_column("Refusal Acc (%)", justify="right", style="bright_green")
        table.add_column("Mean Total Lat (ms)", justify="right", style="blue")

        for mode_name in report.modes_evaluated:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_name)
            if not m:
                continue

            # Format row
            table.add_row(
                m.mode.upper(),
                f"{m.attack_success_rate:.1f}%",
                f"{m.sensitive_info_leakage_rate:.1f}%",
                f"{m.prompt_injection_success_rate:.1f}%",
                f"{m.false_positive_rate:.1f}%",
                f"{m.safe_answer_accuracy:.1f}%",
                f"{m.refusal_accuracy:.1f}%",
                f"{m.avg_latency_total_ms:.1f}",
            )

        console.print("\n")
        console.print(table)
        console.print(f"[dim]Total test samples evaluated: {report.total_test_cases}[/dim]")
        console.print(f"[dim]Results saved to: {report.jsonl_output_path}[/dim]\n")

    @staticmethod
    def generate_research_charts(report: EvaluationRunReport, output_path: str | Path | None = None) -> str:
        """Generate side-by-side Matplotlib bar charts comparing Baseline, Prompt-Only, and Guardrail."""
        modes = report.modes_evaluated
        if not modes:
            return ""

        metrics_list = [report.metrics_by_mode[m] for m in modes if m in report.metrics_by_mode]
        labels = [m.mode.title() for m in metrics_list]

        asrs = [m.attack_success_rate for m in metrics_list]
        silrs = [m.sensitive_info_leakage_rate for m in metrics_list]
        pisrs = [m.prompt_injection_success_rate for m in metrics_list]
        fprs = [m.false_positive_rate for m in metrics_list]
        latencies = [m.avg_latency_total_ms for m in metrics_list]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=300)

        # Plot 1: Security Risk Rates (Lower is Better)
        x = range(len(labels))
        width = 0.2

        ax1.bar([i - 1.5 * width for i in x], asrs, width=width, label="Attack Success (ASR)", color="#e63946")
        ax1.bar([i - 0.5 * width for i in x], silrs, width=width, label="Info Leakage (SILR)", color="#f4a261")
        ax1.bar([i + 0.5 * width for i in x], pisrs, width=width, label="Prompt Injection (PISR)", color="#e76f51")
        ax1.bar([i + 1.5 * width for i in x], fprs, width=width, label="False Positives (FPR)", color="#2a9d8f")

        ax1.set_title("Security Violation Rates (%) [Lower is Better]", fontsize=12, fontweight="bold")
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, fontweight="bold")
        ax1.set_ylabel("Violation Rate (%)")
        ax1.set_ylim(0, 105)
        ax1.grid(axis="y", linestyle="--", alpha=0.5)
        ax1.legend(loc="upper right", fontsize=9)

        # Plot 2: Total Latency Overhead (ms)
        colors = ["#457b9d", "#1d3557", "#2b9348"]
        bars = ax2.bar(labels, latencies, color=colors[: len(labels)], width=0.45)
        ax2.set_title("Average Total Latency (ms)", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Latency (ms)")
        ax2.grid(axis="y", linestyle="--", alpha=0.5)

        for bar in bars:
            height = bar.get_height()
            ax2.annotate(
                f"{height:.1f} ms",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.tight_layout()

        dest_path = (
            Path(output_path)
            if output_path
            else Path(report.jsonl_output_path).parent / f"comparison_chart_{report.timestamp}.png"
        )
        fig.savefig(dest_path)
        plt.close(fig)

        logger.info(f"Research comparison chart saved to: {dest_path}")
        return str(dest_path)

