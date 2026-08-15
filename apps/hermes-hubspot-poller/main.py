"""Entry point for the Hermes->HubSpot sync poller.

One-shot by design, same pattern as apps/hermes-manus-poller/main.py: a scheduler fires this on
an interval; there is no daemon loop, no port, no PID file.

Usage:
    python main.py                 # one tick
    python main.py --dry-run       # log what would happen, change nothing
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Run from any cwd (the scheduler's cwd is not this directory).
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
    parser = argparse.ArgumentParser(description="Hermes->HubSpot sync poller (one tick).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be synced without calling HubSpot or Supabase.",
    )
    args = parser.parse_args()

    if args.dry_run:
        settings.DRY_RUN = True

    _configure_logging()
    summary = poller.run_tick()

    return 1 if summary.get("skipped") else 0


if __name__ == "__main__":
    raise SystemExit(main())
