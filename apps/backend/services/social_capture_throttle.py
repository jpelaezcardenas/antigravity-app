"""In-process throttle for the public social-lead-capture endpoint
(b2c-social-lead-capture, Task 2.3).

No global rate-limiting middleware is actually wired in this backend (confirmed by
reading `main.py` — see design.md's Decision 3, which notes `ARCHITECTURE.md`'s claim
that `slowapi` is mounted is either stale docs or unmounted middleware; either way this
endpoint cannot depend on it existing). So this narrowly-scoped endpoint implements its
own simple throttle:

- an IP window (reject excess requests from the same IP), and
- a phone-number window (a repeat phone number within the window is a silent no-op,
  never a duplicate lead write or duplicate first-contact message once Task 3 wires
  that trigger).

In-process (dict-backed), not Supabase-backed: this endpoint runs on a single Railway
instance and the throttle only needs to survive a few minutes, not a process restart —
a Supabase round-trip on every public hit would be slower and heavier than the abuse it
guards against. A full evaluation of a real global limiter (`slowapi`) is out of scope
here (see design.md's Non-Goals).
"""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict, Optional

# Not derived from measured traffic (none exists yet for this new surface) — chosen to
# allow a real visitor a couple of retries without enabling spam-refresh abuse.
IP_WINDOW_SECONDS = 60
IP_MAX_REQUESTS = 5
PHONE_WINDOW_SECONDS = 600

_ip_hits: Dict[str, Deque[float]] = {}
_phone_last_seen: Dict[str, float] = {}


def reset() -> None:
    """Test-only: clear all throttle state between tests (module-level state would
    otherwise leak across test cases)."""
    _ip_hits.clear()
    _phone_last_seen.clear()


def is_ip_throttled(ip: str, now: Optional[float] = None) -> bool:
    """True if `ip` has already made IP_MAX_REQUESTS requests within IP_WINDOW_SECONDS."""
    now = now if now is not None else time.monotonic()
    hits = _ip_hits.setdefault(ip, deque())
    while hits and now - hits[0] > IP_WINDOW_SECONDS:
        hits.popleft()
    return len(hits) >= IP_MAX_REQUESTS


def record_ip_hit(ip: str, now: Optional[float] = None) -> None:
    now = now if now is not None else time.monotonic()
    _ip_hits.setdefault(ip, deque()).append(now)


def is_phone_repeat(normalized_phone: str, now: Optional[float] = None) -> bool:
    """True if `normalized_phone` was already captured within PHONE_WINDOW_SECONDS —
    the caller must treat this as a no-op, not a new lead/message."""
    now = now if now is not None else time.monotonic()
    last_seen = _phone_last_seen.get(normalized_phone)
    return last_seen is not None and (now - last_seen) <= PHONE_WINDOW_SECONDS


def record_phone_capture(normalized_phone: str, now: Optional[float] = None) -> None:
    now = now if now is not None else time.monotonic()
    _phone_last_seen[normalized_phone] = now
