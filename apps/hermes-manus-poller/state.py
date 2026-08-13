"""Local sidecar mapping operator_task_id -> manus_task_id.

Why a file and not the database: the backend's `mark_dispatched` takes no payload and adding an
`external_task_id` column is out of scope for this change (design.md D2). The sidecar is the
smallest thing that closes the loop without touching the backend.

Losing this file is recoverable and non-destructive: the affected operator task stays `dispatched`
forever and is surfaced by `list_orphans()` for manual resolution. It is deliberately NOT
re-dispatched automatically — re-running a `post_content` task would double-post to Meta.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_STATE_DIR = Path(__file__).parent / "state"
_STATE_FILE = _STATE_DIR / "dispatched.json"


def _load() -> Dict[str, str]:
    if not _STATE_FILE.exists():
        return {}
    try:
        with _STATE_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        # A corrupt sidecar must not crash the tick; treat as empty and let list_orphans surface
        # the resulting mismatch rather than silently re-dispatching.
        logger.error("Could not read %s (%s) — treating as empty.", _STATE_FILE, exc)
        return {}


def _save(mapping: Dict[str, str]) -> None:
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        with _STATE_FILE.open("w", encoding="utf-8") as handle:
            json.dump(mapping, handle, indent=2)
    except Exception as exc:
        logger.error("Could not write %s: %s", _STATE_FILE, exc)


def remember(operator_task_id: str, manus_task_id: str) -> None:
    mapping = _load()
    mapping[operator_task_id] = manus_task_id
    _save(mapping)


def get_manus_task_id(operator_task_id: str) -> Optional[str]:
    return _load().get(operator_task_id)


def forget(operator_task_id: str) -> None:
    mapping = _load()
    if mapping.pop(operator_task_id, None) is not None:
        _save(mapping)


def all_dispatched() -> Dict[str, str]:
    """Every operator_task_id this node has dispatched and not yet resolved."""
    return _load()


def list_orphans(dispatched_task_ids: list) -> list:
    """Operator tasks the backend reports as `dispatched` but that this node has no Manus id for.

    Surfaced for manual resolution; never auto-re-dispatched (see module docstring).
    """
    known = _load()
    return [task_id for task_id in dispatched_task_ids if task_id not in known]
