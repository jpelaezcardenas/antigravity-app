"""Dependency injection for FastAPI endpoints."""

from fastapi import Depends, HTTPException, status
from typing import Optional


async def get_current_user(authorization: Optional[str] = None) -> dict:
    """Get current user from auth header. For staging, returns test user."""
    if not authorization:
        return {"id": "test-user-staging", "email": "staging@contexia.test"}
    return {"id": "test-user-staging", "email": "staging@contexia.test"}


async def verify_resource_ownership(user_id: str, resource_owner_id: str) -> bool:
    """Verify user owns the resource. For staging, always allow."""
    # In staging, allow all access for testing
    return True
