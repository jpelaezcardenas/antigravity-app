"""FastAPI dependency for authenticating Hermes internal endpoints.

Verifies that the incoming request carries a valid HERMES_BRIDGE_TOKEN.
Fails closed: raises RuntimeError at module load time if the env var is unset,
so the application never starts with an unprotected /internal/ route.
"""

import os
import secrets
from typing import Optional

from fastapi import Header, HTTPException, status

_HERMES_BRIDGE_TOKEN: str = os.environ.get("HERMES_BRIDGE_TOKEN", "")

if not _HERMES_BRIDGE_TOKEN:
    raise RuntimeError(
        "HERMES_BRIDGE_TOKEN environment variable is not set. "
        "The /internal/ route group cannot start without it."
    )


def verify_hermes_token(authorization: Optional[str] = Header(default=None)) -> None:
    """FastAPI dependency that validates the Hermes bridge token.

    Expects: Authorization: Bearer <HERMES_BRIDGE_TOKEN>
    Returns None on success; raises HTTP 403 on any mismatch.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ")
    if not secrets.compare_digest(token.encode(), _HERMES_BRIDGE_TOKEN.encode()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Hermes bridge token")
