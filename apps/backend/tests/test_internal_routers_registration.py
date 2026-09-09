"""Guards the /internal router registration in main.py (voicebox-local-voice-adoption).

ARCHITECTURE.md Decisión #22 records a real production incident: the internal-router registration
was wrapped in a `try/except` that logged and continued, it swallowed a `NameError`, and the app
started up reporting itself healthy with both `/internal/*` routes missing. Every poller request
failed against a backend that looked fine.

That wrapper is now gone. This test exists so it cannot come back unnoticed — a missing internal
route must break startup, where a deploy will catch it, rather than surface as a silent outage.

Deliberately source-level. Importing `main` pulls the whole application (~5 minutes on this
machine, because module import triggers KB/pgvector seeding that waits out every embedding
provider's timeout), and this property is about how the code is written, not what it computes at
runtime. The route behaviour itself is covered by tests/test_voice_endpoint_auth.py.
"""

from __future__ import annotations

import re
from pathlib import Path

MAIN_PY = Path(__file__).resolve().parent.parent / "main.py"

_EXPECTED_INTERNAL_ROUTERS = (
    "siigo_sync_router",
    "ingest_file_router",
    "voice_router",
)


def _main_source() -> str:
    return MAIN_PY.read_text(encoding="utf-8")


def _internal_registration_block(source: str) -> str:
    """The lines from the internal-router comment down to the include_router with prefix."""
    start = source.index("# Internal machine-to-machine endpoints")
    end = source.index('app.include_router(_internal_router, prefix="/internal")', start)
    return source[start:end]


def test_all_three_internal_routers_are_registered():
    block = _internal_registration_block(_main_source())
    for router_name in _EXPECTED_INTERNAL_ROUTERS:
        assert (
            f"_internal_router.include_router({router_name})" in block
        ), f"{router_name} is not mounted under /internal"


def test_internal_router_registration_is_not_wrapped_in_try_except():
    """Decisión #22: a swallowed registration failure is a failure, not a warning."""
    block = _internal_registration_block(_main_source())

    assert not re.search(r"^\s*try:", block, re.MULTILINE), (
        "The /internal router registration must not be wrapped in try/except. A swallowed import "
        "error here already caused a live outage (ARCHITECTURE.md Decisión #22): the app started "
        "healthy with the routes missing. Let it raise."
    )
    assert not re.search(r"^\s*except\b", block, re.MULTILINE)


def test_voice_route_path_is_under_internal_not_api_v1():
    """`/internal/*` is not exposed by vercel.json's `/api/v1/:path*` rewrite. Moving this route
    under /api/v1 would publish a machine-to-machine endpoint to the internet."""
    from presentation.voice_endpoints import router

    paths = {route.path for route in router.routes}
    assert "/whatsapp/voice-note" in paths
    for path in paths:
        assert not path.startswith("/api/"), f"{path} must be mounted under /internal, not /api"
