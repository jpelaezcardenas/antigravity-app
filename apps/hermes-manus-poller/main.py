"""Entry point for the Hermes->Manus operator-task poller.

One-shot by design (design.md D1): Windows Task Scheduler fires this every minute via
run_poller.ps1. There is no daemon loop, no port, and no PID file.

Usage:
    python main.py                 # one tick (what the scheduled task runs)
    python main.py --dry-run       # log what would happen, change nothing
    python main.py --once          # explicit no-op alias for one tick, for readability
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Run from any cwd (Task Scheduler's cwd is not this directory).
sys.path.insert(0, str(Path(__file__).parent))

from config import settings  # noqa: E402
import poller  # noqa: E402


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes->Manus operator-task poller (one tick).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be dispatched/reported without calling Manus or the backend.",
    )
    parser.add_argument(
        "--once", action="store_true", help="Run a single tick (default; kept for readability)."
    )
    args = parser.parse_args()

    if args.dry_run:
        settings.DRY_RUN = True

    _configure_logging()
    summary = poller.run_tick()

    # Non-zero only when the poller could not run at all (unconfigured), so Task Scheduler's
    # last-result column is a useful health signal.
    return 1 if summary.get("skipped") else 0


if __name__ == "__main__":
    raise SystemExit(main())
