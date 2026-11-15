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
                f"{m.false_positive_rate:.1f}%",
                f"{m.refusal_accuracy:.1f}%",
            )

        console.print(table_sec)
        console.print("[dim]  Note: ASR = Attack Success Rate (covers harmful evasion & secret leakage), FPR = False Positive Rate, Refusal Acc = Proper Refusal[/dim]\n")

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
        table_qual.add_column("Context Hit Rate ↑", justify="right", style="cyan")
        table_qual.add_column("Faithfulness (%) ↑", justify="right", style="bold cyan")
        table_qual.add_column("Hallucination Rate (%) ↓", justify="right", style="bold red")

        for mode_key in report.modes_evaluated:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_key)
            if not m:
                continue
            table_qual.add_row(
                m.mode.upper(),
                m.model_mode.upper(),
                m.model_name[:20],
                f"{m.context_hit_rate:.1f}%",
                f"{m.avg_faithfulness:.1f}%",
                f"{m.hallucination_rate:.1f}%",
            )

        console.print(table_qual)
        console.print("[dim]  Note: Context Hit Rate = Document retrieval precision, Faithfulness = Grounded in chunks, Hallucination Rate = Out-of-scope guesses[/dim]\n")

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

        # ---------------------------------------------------------
        # Table 4: Defense-in-Depth Layer Interception Report (Pillar 4)
        # ---------------------------------------------------------
        table_stages = Table(
            title="[bold magenta]4. Defense-in-Depth Layer Interception Benchmark (Active Defense Stages)[/bold magenta]",
            header_style="bold magenta",
        )
        table_stages.add_column("Security Mode", style="cyan", no_wrap=True)
        table_stages.add_column("Exec Mode", style="yellow")
        table_stages.add_column("Main Model", style="dim white")
        table_stages.add_column("Input Stage (Query Guard) %", justify="right", style="bold red")
        table_stages.add_column("Context Sanitize %", justify="right", style="cyan")
        table_stages.add_column("Total Intercepted %", justify="right", style="bold green")

        guardrail_modes = [k for k in report.modes_evaluated if "guardrail" in k.lower()]
        target_stage_modes = guardrail_modes if guardrail_modes else report.modes_evaluated

        for mode_key in target_stage_modes:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_key)
            if not m:
                continue
            total_active = m.input_blocked_rate + m.context_sanitized_rate
            table_stages.add_row(
                m.mode.upper(),
                m.model_mode.upper(),
                m.model_name[:20],
                f"{m.input_blocked_rate:.1f}%",
                f"{m.context_sanitized_rate:.1f}%",
                f"{total_active:.1f}%",
            )

        console.print(table_stages)
        console.print("[dim]  Note: Input Guard = Direct injections blocked at boundary; Context Sanitize = Indirect payloads sanitized in retrieved context[/dim]\n")

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
            f"| Security Mode | Exec Mode | Main Model | ASR (%) ↓ | FPR (%) ↓ | Refusal Acc (%) ↑ |",
            f"| :--- | :--- | :--- | :---: | :---: | :---: |",
        ]

        for mode_key in report.modes_evaluated:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_key)
            if not m:
                continue
            lines.append(
                f"| {m.mode.upper()} | {m.model_mode.upper()} | {m.model_name} | "
                f"{m.attack_success_rate:.1f}% | {m.false_positive_rate:.1f}% | "
                f"{m.refusal_accuracy:.1f}% |"
            )

        lines.extend([
            "",
            "> **Pillar 1 Metric Definitions**:",
            "> - **ASR (Attack Success Rate)**: Percentage of malicious, harmful, or unauthorized requests that bypassed defenses (covers harmful evasion & secret extraction).",
            "> - **FPR (False Positive Rate)**: Percentage of benign, safe questions incorrectly blocked by security filters.",
            "> - **Refusal Accuracy**: Proportion of adversarial queries properly identified and refused.",
            "",
            "---",
            "",
            "## 2. Operational Quality & Groundedness Benchmark (RAG Utility)",
            "",
            "| Security Mode | Exec Mode | Main Model | Context Hit Rate ↑ | Faithfulness (%) ↑ | Hallucination Rate (%) ↓ |",
            "| :--- | :--- | :--- | :---: | :---: | :---: |",
        ])

        for mode_key in report.modes_evaluated:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_key)
            if not m:
                continue
            lines.append(
                f"| {m.mode.upper()} | {m.model_mode.upper()} | {m.model_name} | "
                f"{m.context_hit_rate:.1f}% | "
                f"{m.avg_faithfulness:.1f}% | {m.hallucination_rate:.1f}% |"
            )

        lines.extend([
            "",
            "> **Pillar 2 Metric Definitions**:",
            "> - **Context Hit Rate**: Precision of retrieving ground-truth document chunks from Qdrant.",
            "> - **Faithfulness (Groundedness)**: Token-grounding of generated claims directly supported by retrieved context.",
            "> - **Hallucination Rate**: Rate of the model generating ungrounded facts from pre-trained weights when context is absent.",
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
            "## 4. Defense-in-Depth Layer Interception Benchmark (Stage-Wise Breakdown)",
            "",
            "| Security Mode | Exec Mode | Main Model | Input Stage (Query Guard) % | Context Sanitize % | Total Defense Share % |",
            "| :--- | :--- | :--- | :---: | :---: | :---: |",
        ])

        guardrail_modes = [k for k in report.modes_evaluated if "guardrail" in k.lower()]
        target_stage_modes = guardrail_modes if guardrail_modes else report.modes_evaluated

        for mode_key in target_stage_modes:
            m: AggregatedMetrics = report.metrics_by_mode.get(mode_key)
            if not m:
                continue
            total_active = m.input_blocked_rate + m.context_sanitized_rate
            lines.append(
                f"| {m.mode.upper()} | {m.model_mode.upper()} | {m.model_name} | "
                f"{m.input_blocked_rate:.1f}% | {m.context_sanitized_rate:.1f}% | {total_active:.1f}% |"
            )

        lines.extend([
            "",
            "> **Pillar 4 Stage Definitions**:",
            "> - **Input Stage (Query Guard)**: Percentage of intercepted attacks stopped at the perimeter by Meta Llama Prompt Guard 2 or heuristic patterns.",
            "> - **Context Sanitize**: Percentage of intercepted attacks neutralized inside retrieved context chunks (instruction prefixes stripped, delimiter breakouts escaped).",
            "> - **Total Defense Share**: Sum of intercepted threats across active defense layers (always 100.0%).",
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
        labels = []
        for m in metrics_list:
            short_model = m.model_name.split("/")[-1] if m.model_name else "Unknown"
            if len(short_model) > 16:
                short_model = short_model[:14] + "…"
            exec_str = "Hosted" if m.model_mode.lower() == "hosted" else "Local"
            labels.append(f"{m.mode.title()}\n[{exec_str}: {short_model}]")

        x = range(len(labels))

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(max(15, len(labels) * 3.6), 11.0), dpi=300)

        # Plot 1: Security Efficacy (ASR & FPR Lower is Better, Refusal Higher is Better)
        width = 0.25
        asrs = [m.attack_success_rate for m in metrics_list]
        refusals = [m.refusal_accuracy for m in metrics_list]
        fprs = [m.false_positive_rate for m in metrics_list]

        b1 = ax1.bar([i - width for i in x], asrs, width=width, label="Attack Success (ASR) ↓", color="#e63946")
        b2 = ax1.bar([i for i in x], refusals, width=width, label="Refusal Accuracy ↑", color="#2a9d8f")
        b3 = ax1.bar([i + width for i in x], fprs, width=width, label="False Positives (FPR) ↓", color="#f4a261")

        # Value labels for Plot 1
        for bars in (b1, b2, b3):
            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    ax1.annotate(
                        f"{h:.0f}%",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=7,
                        fontweight="bold",
                    )

        ax1.set_title("1. Security Efficacy (%) [ASR/FPR: ↓ | Refusal: ↑]", fontsize=10, fontweight="bold", pad=12)
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, fontweight="bold", fontsize=8)
        ax1.set_ylabel("Percentage (%)")
        ax1.set_ylim(0, 130)  # Generous headroom to prevent legend overlap
        ax1.grid(axis="y", linestyle="--", alpha=0.5)
        ax1.legend(loc="upper center", bbox_to_anchor=(0.5, 0.98), ncol=3, fontsize=7.5, framealpha=0.9)

        # Plot 2: Operational Quality & Groundedness
        w2 = 0.25
        hits = [m.context_hit_rate for m in metrics_list]
        faiths = [m.avg_faithfulness for m in metrics_list]
        hallucinations = [m.hallucination_rate for m in metrics_list]

        q2 = ax2.bar([i - w2 for i in x], hits, width=w2, label="Context Hit Rate ↑", color="#0077b6")
        q3 = ax2.bar(x, faiths, width=w2, label="Faithfulness ↑", color="#55a630")
        q4 = ax2.bar([i + w2 for i in x], hallucinations, width=w2, label="Hallucination Rate ↓", color="#d90429")

        # Value labels for Plot 2
        for bars in (q2, q3, q4):
            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    ax2.annotate(
                        f"{h:.0f}%",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=7,
                        fontweight="bold",
                    )

        ax2.set_title("2. Operational Quality (%) [Faithfulness/Hit: ↑ | Hallucination: ↓]", fontsize=10, fontweight="bold", pad=12)
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, fontweight="bold", fontsize=8)
        ax2.set_ylabel("Score (%)")
        ax2.set_ylim(0, 135)  # Generous headroom to prevent legend overlap
        ax2.grid(axis="y", linestyle="--", alpha=0.5)
        ax2.legend(loc="upper center", bbox_to_anchor=(0.5, 0.98), ncol=3, fontsize=7.5, framealpha=0.9)

        # Plot 3: Latency & Guardrail Overhead Breakdown (ms)
        ret_lats = [m.avg_latency_retrieval_ms for m in metrics_list]
        gen_lats = [m.avg_latency_generation_ms for m in metrics_list]
        overheads = [m.avg_guardrail_overhead_ms for m in metrics_list]

        p1 = ax3.bar(labels, ret_lats, width=0.45, label="Retrieval (Qdrant)", color="#457b9d")
        p2 = ax3.bar(labels, gen_lats, width=0.45, bottom=ret_lats, label="Generation (LLM)", color="#1d3557")
        bottom_sum = [ret_lats[i] + gen_lats[i] for i in range(len(labels))]
        p3 = ax3.bar(labels, overheads, width=0.45, bottom=bottom_sum, label="Guardrail Overhead", color="#e76f51")

        max_lat = max(m.avg_latency_total_ms for m in metrics_list) if metrics_list else 1000.0
        ax3.set_title("3. Latency Breakdown (ms)", fontsize=10, fontweight="bold", pad=12)
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels, fontweight="bold", fontsize=8)
        ax3.set_ylabel("Latency (ms)")
        ax3.set_ylim(0, max_lat * 1.35)  # 35% empty space above highest bar
        ax3.grid(axis="y", linestyle="--", alpha=0.5)
        ax3.legend(loc="upper left", bbox_to_anchor=(0.02, 0.98), fontsize=7.5, framealpha=0.9)

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

        # Plot 4: Defense-in-Depth Layer Interception Breakdown (%) [Guardrail Only]
        guardrail_metrics = [m for m in metrics_list if "guardrail" in m.mode.lower()]
        target_g_metrics = guardrail_metrics if guardrail_metrics else metrics_list

        stage_names = ["Input Guard\n(Query)", "Context\nSanitizer"]
        stage_colors = ["#e63946", "#0077b6"]

        if len(target_g_metrics) == 1:
            # Single guardrail mode: plot each active stage as a distinct colored bar
            gm = target_g_metrics[0]
            stage_values = [gm.input_blocked_rate, gm.context_sanitized_rate]
            s_bars = ax4.bar(range(2), stage_values, color=stage_colors, width=0.45)
            for bar, val in zip(s_bars, stage_values):
                ax4.annotate(
                    f"{val:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, val),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8.5,
                    fontweight="bold",
                )
            ax4.set_xticks(range(2))
            ax4.set_xticklabels(stage_names, fontweight="bold", fontsize=8.5)
            short_g_model = gm.model_name.split("/")[-1] if gm.model_name else "Unknown"
            exec_g_str = "Hosted" if gm.model_mode.lower() == "hosted" else "Local"
            ax4.set_title(f"4. Guardrail Defense Stages [% of Intercepted Threats]\n[{exec_g_str}: {short_g_model}]", fontsize=9.5, fontweight="bold", pad=12)
        else:
            # Multiple guardrail modes: group bars per stage
            num_gm = len(target_g_metrics)
            gw = 0.8 / num_gm
            for g_idx, gm in enumerate(target_g_metrics):
                short_g_model = gm.model_name.split("/")[-1] if gm.model_name else "Unknown"
                exec_g_str = "Hosted" if gm.model_mode.lower() == "hosted" else "Local"
                g_label = f"{gm.mode.title()} ({exec_g_str})"
                stage_values = [gm.input_blocked_rate, gm.context_sanitized_rate]
                offset = (g_idx - (num_gm - 1) / 2) * gw
                s_bars = ax4.bar([i + offset for i in range(2)], stage_values, width=gw, label=g_label)
                for bar, val in zip(s_bars, stage_values):
                    if val > 0:
                        ax4.annotate(
                            f"{val:.0f}%",
                            xy=(bar.get_x() + bar.get_width() / 2, val),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha="center",
                            va="bottom",
                            fontsize=7.5,
                            fontweight="bold",
                        )
            ax4.set_xticks(range(2))
            ax4.set_xticklabels(stage_names, fontweight="bold", fontsize=8.5)
            ax4.set_title("4. Guardrail Defense Stages [% of Intercepted Threats]", fontsize=9.5, fontweight="bold", pad=12)
            ax4.legend(loc="upper right", fontsize=7.5, framealpha=0.9)

        ax4.set_ylabel("Threats Intercepted (%)")
        ax4.set_ylim(0, 130)  # Generous headroom to keep labels clean
        ax4.grid(axis="y", linestyle="--", alpha=0.5)

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
