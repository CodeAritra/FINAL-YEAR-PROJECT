"""
Standalone Chart Generator from Benchmark Markdown Reports.
Parses the four benchmark tables from any evaluation .md file and renders:
1. Four individual publication-ready charts (PNG):
   - 1_security_efficacy.png
   - 2_operational_quality.png
   - 3_latency_breakdown.png
   - 4_defense_in_depth.png
2. One combined 2x2 publication figure (PNG):
   - combined_comparison_chart.png

Usage:
  python scripts/render_charts_from_md.py <path_to_markdown_file.md> [--output-dir <dir>]
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import Any

# Ensure matplotlib cache is local before importing matplotlib
_cache_dir = Path(__file__).resolve().parent.parent / "storage" / "cache" / "matplotlib"
_cache_dir.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(_cache_dir)

import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt


def parse_float(val: Any, default: float = 0.0) -> float:
    """Parse numeric values from strings containing %, ms, etc."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    s = s.replace("%", "").replace("ms", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return default


def parse_markdown_tables(md_text: str) -> list[dict[str, Any]]:
    """
    Extracts all markdown tables from text along with preceding heading context.
    Returns list of {'heading': str, 'headers': list[str], 'rows': list[dict[str, str]]}
    """
    lines = md_text.splitlines()
    tables = []
    current_heading = "General Benchmark"
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#"):
            current_heading = line.lstrip("#").strip()
            i += 1
            continue

        # Look for table header
        if line.startswith("|") and line.endswith("|") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Verify separator line (e.g. | :--- | :---: |)
            if next_line.startswith("|") and next_line.endswith("|") and ("---" in next_line or "-:" in next_line):
                headers = [h.strip() for h in line.strip("|").split("|")]
                rows = []
                j = i + 2
                while j < len(lines):
                    row_line = lines[j].strip()
                    if not (row_line.startswith("|") and row_line.endswith("|")):
                        break
                    cells = [c.strip() for c in row_line.strip("|").split("|")]
                    # Map to headers
                    row_dict = {}
                    for idx, h in enumerate(headers):
                        row_dict[h] = cells[idx] if idx < len(cells) else ""
                    rows.append(row_dict)
                    j += 1
                
                tables.append({
                    "heading": current_heading,
                    "headers": headers,
                    "rows": rows
                })
                i = j
                continue
        i += 1
    return tables


def identify_benchmark_tables(tables: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    """
    Identifies the 4 standard benchmark tables by analyzing column headers and heading text.
    Returns dict with keys: 'table1_sec', 'table2_ops', 'table3_lat', 'table4_def'
    """
    identified = {
        "table1_sec": [],
        "table2_ops": [],
        "table3_lat": [],
        "table4_def": [],
    }

    for t in tables:
        headers_lower = [h.lower() for h in t["headers"]]
        heading_lower = t["heading"].lower()

        # Table 1: Security Efficacy (ASR, Refusal, FPR)
        if any("asr" in h for h in headers_lower) or ("security" in heading_lower and "efficacy" in heading_lower):
            identified["table1_sec"] = t["rows"]
        # Table 2: Operational Quality (Context Hit Rate, Faithfulness, Hallucination)
        elif any("faithfulness" in h or "grounded" in h for h in headers_lower) or ("operational" in heading_lower and "quality" in heading_lower):
            identified["table2_ops"] = t["rows"]
        # Table 3: Latency & Cost (Retrieval Lat, Generation Lat, Overhead)
        elif any("retrieval lat" in h or "generation lat" in h or "overhead" in h for h in headers_lower) or ("latency" in heading_lower and "cost" in heading_lower):
            identified["table3_lat"] = t["rows"]
        # Table 4: Defense-in-Depth (Input Stage, Context Sanitize, Defense Share)
        elif any("input stage" in h or "context sanitize" in h or "defense share" in h for h in headers_lower) or ("defense-in-depth" in heading_lower or "stage" in heading_lower):
            identified["table4_def"] = t["rows"]

    return identified


def get_field(row: dict[str, str], *candidate_keywords: str) -> str:
    """Find a value in a row by matching candidate substrings in the header keys."""
    for cand in candidate_keywords:
        cand_l = cand.lower()
        for k, v in row.items():
            if cand_l in k.lower():
                return v
    return ""


def build_mode_label(row: dict[str, str]) -> str:
    """Build a clean multi-line label for x-axis ticks."""
    mode = get_field(row, "security mode", "mode") or "Unknown"
    exec_mode = get_field(row, "exec mode", "execution mode") or "Hosted"
    model = get_field(row, "main model", "model") or ""

    short_model = model.split("/")[-1] if model else ""
    if len(short_model) > 16:
        short_model = short_model[:14] + "…"

    exec_str = "Hosted" if "host" in exec_mode.lower() else "Local"
    if short_model:
        return f"{mode.title()}\n[{exec_str}: {short_model}]"
    return f"{mode.title()}\n[{exec_str}]"


# ==============================================================================
# INDIVIDUAL CHART RENDERERS
# ==============================================================================

def plot_security_efficacy(rows: list[dict[str, str]], ax: plt.Axes) -> None:
    """Plot 1: Security Efficacy Benchmark (ASR, Refusal Acc, FPR)."""
    if not rows:
        ax.text(0.5, 0.5, "No Security Data Available", ha="center", va="center")
        return

    labels = [build_mode_label(r) for r in rows]
    x = range(len(labels))
    width = 0.25

    asrs = [parse_float(get_field(r, "asr")) for r in rows]
    refusals = [parse_float(get_field(r, "refusal")) for r in rows]
    fprs = [parse_float(get_field(r, "fpr")) for r in rows]

    b1 = ax.bar([i - width for i in x], asrs, width=width, label="Attack Success (ASR) ↓", color="#e63946")
    b2 = ax.bar([i for i in x], refusals, width=width, label="Refusal Accuracy ↑", color="#2a9d8f")
    b3 = ax.bar([i + width for i in x], fprs, width=width, label="False Positives (FPR) ↓", color="#f4a261")

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.annotate(
                    f"{h:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                )

    ax.set_title("1. Security Efficacy (%) [ASR/FPR: ↓ | Refusal: ↑]", fontsize=11, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontweight="bold", fontsize=9)
    ax.set_ylabel("Percentage (%)")
    ax.set_ylim(0, 130)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.98), ncol=3, fontsize=8.5, framealpha=0.9)


def plot_operational_quality(rows: list[dict[str, str]], ax: plt.Axes) -> None:
    """Plot 2: Operational Quality & Groundedness (Hit Rate, Faithfulness, Hallucination Rate)."""
    if not rows:
        ax.text(0.5, 0.5, "No Operational Quality Data Available", ha="center", va="center")
        return

    labels = [build_mode_label(r) for r in rows]
    x = range(len(labels))
    w2 = 0.25

    hits = [parse_float(get_field(r, "context hit", "hit rate")) for r in rows]
    faiths = [parse_float(get_field(r, "faithfulness")) for r in rows]
    hallucinations = [parse_float(get_field(r, "hallucination")) for r in rows]

    q1 = ax.bar([i - w2 for i in x], hits, width=w2, label="Context Hit Rate ↑", color="#0077b6")
    q2 = ax.bar(x, faiths, width=w2, label="Faithfulness ↑", color="#55a630")
    q3 = ax.bar([i + w2 for i in x], hallucinations, width=w2, label="Hallucination Rate ↓", color="#d90429")

    for bars in (q1, q2, q3):
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.annotate(
                    f"{h:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                )

    ax.set_title("2. Operational Quality (%) [Faithfulness/Hit: ↑ | Hallucination: ↓]", fontsize=11, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontweight="bold", fontsize=9)
    ax.set_ylabel("Score (%)")
    ax.set_ylim(0, 135)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.98), ncol=3, fontsize=8.5, framealpha=0.9)


def plot_latency_breakdown(rows: list[dict[str, str]], ax: plt.Axes) -> None:
    """Plot 3: Latency & Guardrail Overhead Breakdown (ms)."""
    if not rows:
        ax.text(0.5, 0.5, "No Latency Data Available", ha="center", va="center")
        return

    labels = [build_mode_label(r) for r in rows]
    x = range(len(labels))

    ret_lats = [parse_float(get_field(r, "retrieval lat")) for r in rows]
    gen_lats = [parse_float(get_field(r, "generation lat")) for r in rows]
    overheads = [parse_float(get_field(r, "guardrail overhead", "overhead")) for r in rows]
    totals = [parse_float(get_field(r, "total latency")) for r in rows]

    p1 = ax.bar(labels, ret_lats, width=0.45, label="Retrieval (Qdrant)", color="#457b9d")
    p2 = ax.bar(labels, gen_lats, width=0.45, bottom=ret_lats, label="Generation (LLM)", color="#1d3557")
    bottom_sum = [ret_lats[i] + gen_lats[i] for i in range(len(labels))]
    p3 = ax.bar(labels, overheads, width=0.45, bottom=bottom_sum, label="Guardrail Overhead", color="#e76f51")

    max_lat = max(totals) if totals and max(totals) > 0 else 1000.0
    ax.set_title("3. Latency Breakdown (ms)", fontsize=11, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontweight="bold", fontsize=9)
    ax.set_ylabel("Latency (ms)")
    ax.set_ylim(0, max_lat * 1.35)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.98), fontsize=8.5, framealpha=0.9)

    for i, t in enumerate(totals):
        total_h = t if t > 0 else (ret_lats[i] + gen_lats[i] + overheads[i])
        ax.annotate(
            f"{total_h:.0f} ms",
            xy=(i, total_h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=8.5,
        )


def plot_defense_stages(rows: list[dict[str, str]], ax: plt.Axes) -> None:
    """Plot 4: Defense-in-Depth Layer Interception Breakdown (%)."""
    if not rows:
        ax.text(0.5, 0.5, "No Defense Stage Data Available", ha="center", va="center")
        return

    # Check if output stage is present in the data
    has_output = any(
        parse_float(get_field(r, "output stage", "output block", "output")) > 0 or bool(get_field(r, "output"))
        for r in rows
    )

    if has_output:
        stage_names = ["Input Guard\n(Query)", "Context\nSanitizer", "Output\nScanner"]
        stage_colors = ["#e63946", "#0077b6", "#2a9d8f"]
    else:
        stage_names = ["Input Guard\n(Query)", "Context\nSanitizer"]
        stage_colors = ["#e63946", "#0077b6"]

    num_stages = len(stage_names)

    if len(rows) == 1:
        # Single guardrail mode
        r = rows[0]
        inp_val = parse_float(get_field(r, "input stage", "input guard", "input"))
        ctx_val = parse_float(get_field(r, "context sanitize", "context"))
        if has_output:
            out_val = parse_float(get_field(r, "output stage", "output block", "output"))
            stage_values = [inp_val, ctx_val, out_val]
        else:
            stage_values = [inp_val, ctx_val]

        s_bars = ax.bar(range(num_stages), stage_values, color=stage_colors, width=0.45)
        for bar, val in zip(s_bars, stage_values):
            ax.annotate(
                f"{val:.1f}%",
                xy=(bar.get_x() + bar.get_width() / 2, val),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )
        ax.set_xticks(range(num_stages))
        ax.set_xticklabels(stage_names, fontweight="bold", fontsize=9.5)
        model = get_field(r, "main model", "model") or ""
        short_model = model.split("/")[-1] if model else "Model"
        exec_str = "Hosted" if "host" in (get_field(r, "exec mode") or "").lower() else "Local"
        ax.set_title(f"4. Guardrail Defense Stages [% of Intercepted Threats]\n[{exec_str}: {short_model}]", fontsize=10.5, fontweight="bold", pad=12)
    else:
        # Multiple rows / modes
        num_rows = len(rows)
        gw = 0.8 / num_rows
        for idx, r in enumerate(rows):
            mode = get_field(r, "security mode") or "Guardrail"
            exec_str = "Hosted" if "host" in (get_field(r, "exec mode") or "").lower() else "Local"
            label = f"{mode.title()} ({exec_str})"
            inp_val = parse_float(get_field(r, "input stage", "input guard", "input"))
            ctx_val = parse_float(get_field(r, "context sanitize", "context"))
            if has_output:
                out_val = parse_float(get_field(r, "output stage", "output block", "output"))
                stage_values = [inp_val, ctx_val, out_val]
            else:
                stage_values = [inp_val, ctx_val]

            offset = (idx - (num_rows - 1) / 2) * gw
            s_bars = ax.bar([i + offset for i in range(num_stages)], stage_values, width=gw, label=label)
            for bar, val in zip(s_bars, stage_values):
                if val > 0:
                    ax.annotate(
                        f"{val:.1f}%",
                        xy=(bar.get_x() + bar.get_width() / 2, val),
                        xytext=(0, 4),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                        fontweight="bold",
                    )
        ax.set_xticks(range(num_stages))
        ax.set_xticklabels(stage_names, fontweight="bold", fontsize=9.5)
        ax.set_title("4. Guardrail Defense Stages [% of Intercepted Threats]", fontsize=10.5, fontweight="bold", pad=12)
        ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

    ax.set_ylabel("Threats Intercepted (%)")
    ax.set_ylim(0, 130)
    ax.grid(axis="y", linestyle="--", alpha=0.5)


# ==============================================================================
# MAIN EXPORT WORKFLOW
# ==============================================================================

def render_all_charts(md_path: str | Path, output_dir: str | Path | None = None) -> list[str]:
    """
    Parses tables from md_path and writes:
    - 4 distinct individual charts (PNG)
    - 1 unified 2x2 publication chart (PNG)
    Returns list of paths of generated images.
    """
    md_file = Path(md_path).resolve()
    if not md_file.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_file}")

    target_dir = Path(output_dir).resolve() if output_dir else md_file.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    content = md_file.read_text(encoding="utf-8")
    tables = parse_markdown_tables(content)
    identified = identify_benchmark_tables(tables)

    generated_paths = []
    base_stem = md_file.stem.replace("eval_run_", "chart_")

    print(f"\n[*] Parsing Markdown: {md_file.name}")
    print(f"[*] Found {len(tables)} tables total.")
    print(f"    - Table 1 (Security Efficacy): {len(identified['table1_sec'])} rows")
    print(f"    - Table 2 (Operational Quality): {len(identified['table2_ops'])} rows")
    print(f"    - Table 3 (Latency & Cost): {len(identified['table3_lat'])} rows")
    print(f"    - Table 4 (Defense Stages): {len(identified['table4_def'])} rows")

    # 1. Individual Chart: Security Efficacy
    fig1, ax1 = plt.subplots(figsize=(8.0, 5.5), dpi=300)
    plot_security_efficacy(identified["table1_sec"], ax1)
    plt.tight_layout()
    p1 = target_dir / f"{base_stem}_1_security_efficacy.png"
    fig1.savefig(p1)
    plt.close(fig1)
    generated_paths.append(str(p1))
    print(f"    [+] Created: {p1.name}")

    # 2. Individual Chart: Operational Quality
    fig2, ax2 = plt.subplots(figsize=(8.0, 5.5), dpi=300)
    plot_operational_quality(identified["table2_ops"], ax2)
    plt.tight_layout()
    p2 = target_dir / f"{base_stem}_2_operational_quality.png"
    fig2.savefig(p2)
    plt.close(fig2)
    generated_paths.append(str(p2))
    print(f"    [+] Created: {p2.name}")

    # 3. Individual Chart: Latency Breakdown
    fig3, ax3 = plt.subplots(figsize=(8.0, 5.5), dpi=300)
    plot_latency_breakdown(identified["table3_lat"], ax3)
    plt.tight_layout()
    p3 = target_dir / f"{base_stem}_3_latency_breakdown.png"
    fig3.savefig(p3)
    plt.close(fig3)
    generated_paths.append(str(p3))
    print(f"    [+] Created: {p3.name}")

    # 4. Individual Chart: Defense Stages
    fig4, ax4 = plt.subplots(figsize=(8.0, 5.5), dpi=300)
    plot_defense_stages(identified["table4_def"], ax4)
    plt.tight_layout()
    p4 = target_dir / f"{base_stem}_4_defense_in_depth.png"
    fig4.savefig(p4)
    plt.close(fig4)
    generated_paths.append(str(p4))
    print(f"    [+] Created: {p4.name}")

    # 5. Combined 2x2 Publication Figure
    num_modes = max(len(identified["table1_sec"]), len(identified["table2_ops"]), 3)
    fig_all, ((c_ax1, c_ax2), (c_ax3, c_ax4)) = plt.subplots(2, 2, figsize=(max(15, num_modes * 3.6), 11.0), dpi=300)
    plot_security_efficacy(identified["table1_sec"], c_ax1)
    plot_operational_quality(identified["table2_ops"], c_ax2)
    plot_latency_breakdown(identified["table3_lat"], c_ax3)
    plot_defense_stages(identified["table4_def"], c_ax4)
    plt.tight_layout()
    p_all = target_dir / f"{base_stem}_combined_comparison_chart.png"
    fig_all.savefig(p_all)
    plt.close(fig_all)
    generated_paths.append(str(p_all))
    print(f"    [+] Created (Combined 2x2 Figure): {p_all.name}")

    print(f"\n[SUCCESS] Rendered 4 individual charts + 1 combined 2x2 publication chart to: {target_dir}")
    return generated_paths


def main():
    parser = argparse.ArgumentParser(description="Generate 4 individual research charts + 1 combined chart from a benchmark Markdown file.")
    parser.add_argument("markdown_file", type=str, help="Path to input .md file containing benchmark tables.")
    parser.add_argument("--output-dir", "-o", type=str, default=None, help="Directory to save generated chart PNGs.")

    args = parser.parse_args()
    render_all_charts(args.markdown_file, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
