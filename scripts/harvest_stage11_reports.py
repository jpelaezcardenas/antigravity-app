"""Harvest completed Stage 11 deployment reports into the contexia-brain inbox.

Part of OpenSpec change `adopt-gbrain-second-brain` (capability `second-brain-raw-loop`).

Stage 11 deployment reports live at:
    openspec/changes/<id>/reports/*.md            (active changes)
    openspec/changes/archive/<dated-id>/reports/*.md   (archived changes)

Their learnings otherwise sit inert once a change is archived. This script copies a
reference (path + first heading + summary excerpt) of each report into the SEPARATE
`contexia-brain` repo's `raw/` folder (sibling to this repo) so the next librarian loop /
GBrain Dream Cycle can compound them into the brain.

Reports are read from this repo (antigravity-app). The harvest destination is a
DIFFERENT repo on purpose (see contexia-brain/README.md): antigravity-app's main branch
auto-deploys to Vercel/Railway on every push, so brain content must never live here —
autonomous Dream Cycle commits to the brain repo must never be able to trigger a deploy.

A ledger (`<brain-dir>/raw/_harvested.json`) records which reports were already harvested,
keyed by report path + content hash, so re-runs never duplicate an already-harvested report
(spec scenario: "Harvest does not duplicate already-harvested reports").

Idempotent and non-destructive: it only creates/refreshes files under the brain repo's
`raw/`, never touches the reports themselves. Run manually or on a schedule.

Usage:
    python scripts/harvest_stage11_reports.py [--repo-root .] [--brain-dir ../contexia-brain] [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

LEDGER_NAME = "_harvested.json"
HARVEST_PREFIX = "stage11-"


@dataclass(frozen=True)
class Report:
    """A single Stage 11 deployment report discovered on disk."""

    path: Path
    content: str

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    @property
    def ledger_key(self) -> str:
        # Path + hash: re-harvest only if the report content actually changed.
        return f"{self.path.as_posix()}::{self.content_hash}"

    @property
    def title(self) -> str:
        for line in self.content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
        return self.path.stem

    def excerpt(self, max_chars: int = 800) -> str:
        body = self.content.strip()
        return body if len(body) <= max_chars else body[:max_chars].rstrip() + "\n\n…(truncated)"


def find_reports(repo_root: Path) -> list[Report]:
    """Locate every Stage 11 report under active and archived OpenSpec changes."""
    changes_dir = repo_root / "openspec" / "changes"
    reports: list[Report] = []
    if not changes_dir.is_dir():
        return reports
    for report_path in sorted(changes_dir.glob("**/reports/*.md")):
        try:
            content = report_path.read_text(encoding="utf-8")
        except OSError:
            continue
        reports.append(Report(path=report_path.relative_to(repo_root), content=content))
    return reports


def load_ledger(raw_dir: Path) -> dict[str, str]:
    ledger_path = raw_dir / LEDGER_NAME
    if not ledger_path.is_file():
        return {}
    try:
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_ledger(raw_dir: Path, ledger: dict[str, str]) -> None:
    ledger_path = raw_dir / LEDGER_NAME
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def harvest_filename(report: Report) -> str:
    slug = report.path.as_posix().replace("/", "__").removesuffix(".md")
    return f"{HARVEST_PREFIX}{slug}.md"


def render_harvest(report: Report) -> str:
    return (
        f"# Harvested Stage 11 report: {report.title}\n\n"
        f"_Source: `{report.path.as_posix()}` — harvested {date.today().isoformat()}._\n\n"
        f"> This is a capture for the second brain. The source report is unchanged.\n\n"
        f"---\n\n{report.excerpt()}\n"
    )


def harvest(repo_root: Path, brain_dir: Path, dry_run: bool = False) -> tuple[int, int]:
    """Harvest new reports from repo_root into brain_dir/raw/. Returns (harvested, skipped)."""
    raw_dir = brain_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    ledger = load_ledger(raw_dir)

    harvested = 0
    skipped = 0
    for report in find_reports(repo_root):
        if report.ledger_key in ledger:
            skipped += 1
            continue
        target = raw_dir / harvest_filename(report)
        if dry_run:
            print(f"[dry-run] would harvest {report.path} -> {target}")
        else:
            target.write_text(render_harvest(report), encoding="utf-8")
            ledger[report.ledger_key] = target.name
            print(f"harvested {report.path} -> {target}")
        harvested += 1

    if not dry_run:
        save_ledger(raw_dir, ledger)
    return harvested, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="antigravity-app root (default: current dir)")
    parser.add_argument(
        "--brain-dir",
        default="../contexia-brain",
        help="contexia-brain repo root, relative to --repo-root (default: ../contexia-brain, a sibling repo)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report actions without writing files")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    brain_dir = (repo_root / args.brain_dir).resolve()

    harvested, skipped = harvest(repo_root, brain_dir, dry_run=args.dry_run)
    print(f"\nBrain dir: {brain_dir}")
    print(f"Done. Harvested: {harvested}, already-harvested (skipped): {skipped}")


if __name__ == "__main__":
    main()
