"""
Qdrant Vector Database Cleanup Utility.
Purges or recreates vector collections (baseline_rag, secured_rag, or custom/all collections).
Provides confirmation safeguards and reporting on deleted points.

Usage:
    python scripts/clean_qdrant.py               # Interactive prompt to clean baseline & secured
    python scripts/clean_qdrant.py --recreate    # Clean and immediately recreate empty collections
    python scripts/clean_qdrant.py --all         # Clean ALL collections found on Qdrant cluster
    python scripts/clean_qdrant.py -c custom_col # Clean a specific collection
    python scripts/clean_qdrant.py --force       # Bypass interactive confirmation
"""

import sys
import argparse
from pathlib import Path
from typing import List

# Ensure parent directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config.settings import settings
from database.qdrant_manager import QdrantManager
from qdrant_client.http import models

try:
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Confirm
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def print_msg(msg: str, style: str = "") -> None:
    if HAS_RICH:
        console.print(f"[{style}]{msg}[/{style}]" if style else msg)
    else:
        print(msg)


def clean_qdrant(
    collections: List[str] | None = None,
    clean_all: bool = False,
    recreate: bool = False,
    force: bool = False,
) -> None:
    """Purge specified or all collections from Qdrant."""
    print_msg("\n[*] Qdrant Database Cleanup Utility", style="bold cyan")
    print_msg(f"Target URL: {settings.qdrant_url}", style="dim")

    qm = QdrantManager()

    # Discover existing collections on server
    try:
        remote_cols = [c.name for c in qm.client.get_collections().collections]
    except Exception as e:
        print_msg(f"[!] Failed to connect to Qdrant or fetch collections: {e}", style="bold red")
        sys.exit(1)

    if not remote_cols:
        print_msg("No collections found in Qdrant. Nothing to clean.", style="yellow")
        return

    # Determine target collections
    if clean_all:
        target_cols = remote_cols
    elif collections:
        target_cols = collections
    else:
        # Default: target baseline and secured collections defined in settings
        default_targets = [settings.qdrant_collection_baseline, settings.qdrant_collection_secured]
        target_cols = [c for c in default_targets if c in remote_cols]
        if not target_cols:
            target_cols = [c for c in default_targets]

    # Gather metrics before deletion
    table_data = []
    total_points = 0
    for name in target_cols:
        exists = name in remote_cols
        if exists:
            info = qm.get_collection_info(name)
            pts = info.get("points_count", 0)
            total_points += pts
            table_data.append((name, str(pts), "Found"))
        else:
            table_data.append((name, "0", "Not Present"))

    # Display preview table
    if HAS_RICH:
        tbl = Table(title="Collections Targeted for Cleanup", header_style="bold magenta")
        tbl.add_column("Collection Name", style="cyan")
        tbl.add_column("Points Count", style="bold white", justify="right")
        tbl.add_column("Status", style="yellow")
        for row in table_data:
            tbl.add_row(*row)
        console.print(tbl)
    else:
        print("\nCollections targeted for cleanup:")
        for name, pts, st in table_data:
            print(f"  - {name}: {pts} points ({st})")

    # Safety confirmation prompt
    if not force:
        warning_prompt = (
            f"\nAre you sure you want to delete {len(target_cols)} collection(s) "
            f"containing approximately {total_points} total points?"
        )
        if HAS_RICH:
            confirmed = Confirm.ask(warning_prompt, default=False)
        else:
            ans = input(f"{warning_prompt} [y/N]: ").strip().lower()
            confirmed = ans in ("y", "yes")

        if not confirmed:
            print_msg("[!] Cleanup cancelled by user.", style="yellow")
            return

    # Execute deletion and optional recreation
    print_msg("\n[*] Deleting collections...", style="bold yellow")
    results = []

    for name in target_cols:
        if name in remote_cols:
            success = qm.delete_collection(name)
            del_status = "Deleted" if success else "Failed to Delete"
        else:
            del_status = "Skipped (Not Found)"

        recreated_status = "-"
        if recreate:
            try:
                qm.client.create_collection(
                    collection_name=name,
                    vectors_config=models.VectorParams(
                        size=settings.gemini_embedding_dimension,
                        distance=models.Distance.COSINE,
                    ),
                )
                recreated_status = f"Recreated (dim: {settings.gemini_embedding_dimension})"
            except Exception as e:
                recreated_status = f"Recreate Error ({e})"

        results.append((name, del_status, recreated_status))

    # Display final report
    if HAS_RICH:
        res_table = Table(title="Cleanup Execution Results", header_style="bold green")
        res_table.add_column("Collection Name", style="cyan")
        res_table.add_column("Deletion Status", style="bold white")
        res_table.add_column("Recreation Status", style="magenta")
        for r in results:
            res_table.add_row(*r)
        console.print(res_table)
    else:
        print("\nCleanup Results:")
        for name, del_st, rec_st in results:
            print(f"  - {name}: {del_st} | {rec_st}")

    print_msg("\n[OK] Qdrant cleanup completed successfully.\n", style="bold green")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up and purge collections from Qdrant vector database."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Purge ALL collections found in the Qdrant cluster.",
    )
    parser.add_argument(
        "--collection",
        "-c",
        nargs="+",
        help="Specific collection name(s) to purge (e.g. -c baseline_rag secured_rag).",
    )
    parser.add_argument(
        "--recreate",
        "-r",
        action="store_true",
        help="Recreate fresh, empty collections with configured embedding dimension after deletion.",
    )
    parser.add_argument(
        "--force",
        "-f",
        "-y",
        action="store_true",
        help="Skip interactive confirmation prompt.",
    )

    args = parser.parse_args()

    clean_qdrant(
        collections=args.collection,
        clean_all=args.all,
        recreate=args.recreate,
        force=args.force,
    )


if __name__ == "__main__":
    main()

