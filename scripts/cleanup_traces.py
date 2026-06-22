"""Trace DB cleanup script.

Deletes trace rows older than ``--days`` from ``data/traces.db``. Designed to be
run from cron / Task Scheduler.

Usage::

    conda activate ai-agent
    python -m scripts.cleanup_traces --days 30
    python -m scripts.cleanup_traces --days 7 --dry-run
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.config import get_settings


def cleanup(days: int, dry_run: bool = False) -> dict[str, int | str]:
    settings = get_settings()
    db_path = Path(settings.tracing_db_path)
    if not db_path.exists():
        return {"db_path": str(db_path), "deleted": 0, "note": "database not found"}

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        # Count first so dry-run can report.
        before = conn.execute(
            "SELECT COUNT(*) FROM traces WHERE started_at < ?", (cutoff,)
        ).fetchone()[0]

        if dry_run:
            return {
                "db_path": str(db_path),
                "cutoff": cutoff,
                "would_delete": int(before),
                "deleted": 0,
            }

        conn.execute("DELETE FROM traces WHERE started_at < ?", (cutoff,))
        conn.execute("VACUUM")
        conn.commit()

    return {
        "db_path": str(db_path),
        "cutoff": cutoff,
        "deleted": int(before),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete old trace records.")
    parser.add_argument("--days", type=int, default=30, help="Delete traces older than N days.")
    parser.add_argument("--dry-run", action="store_true", help="Report only, do not delete.")
    args = parser.parse_args()

    result = cleanup(days=args.days, dry_run=args.dry_run)
    print(result)


if __name__ == "__main__":
    main()
