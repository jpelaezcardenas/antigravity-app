"""Entry point for the Hermes Gmail attachment ingestion poller.

One-shot by design — a scheduler fires this every 15 minutes.

Usage:
    python main.py                 # one tick
    python main.py --dry-run       # log what would be ingested, change nothing
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

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
    parser = argparse.ArgumentParser(
        description="Hermes Gmail attachment ingestion poller (one tick)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be ingested without downloading, posting, or labeling.",
    )
    args = parser.parse_args()

    if args.dry_run:
        settings.DRY_RUN = True

    _configure_logging()
    summary = poller.run_tick()

    return 1 if summary.get("skipped") else 0


if __name__ == "__main__":
    raise SystemExit(main())
