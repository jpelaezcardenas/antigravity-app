"""
Unit tests for TenantContextMiddleware.

Tests:
1. Middleware correctly extracts tenant_id from JWT
2. Middleware injects tenant_id into request.state
3. Middleware defaults to "default-tenant" when no JWT provided
4. Middleware handles invalid JWT gracefully
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from core.tenant_middleware import TenantContextMiddleware
from core.security import create_access_token


@pytest.fixture
def app_with_middleware():
    """Create FastAPI app with TenantContextMiddleware and a test endpoint."""
    app = FastAPI()
    app.add_middleware(TenantContextMiddleware)

    @app.get("/test")
    async def test_endpoint(request: Request):
        return {
            "tenant_id": request.state.tenant_id,
            "user_id": request.state.user_id,
        }

    return app


@pytest.fixture
def client(app_with_middleware):
    """FastAPI test client."""
    return TestClient(app_with_middleware)


def test_middleware_extracts_tenant_id_from_jwt(client):
    """
    Test: Middleware correctly extracts tenant_id from JWT.

    Given: A JWT token with tenant_id = "org-1" and sub = "user-1"
    When: Request is made with this token
    Then: request.state.tenant_id should be "org-1"
    """
    # Create token with tenant_id
    token = create_access_token({"sub": "user-1", "tenant_id": "org-1"})

    # Make request
    response = client.get("/test", headers={"Authorization": f"Bearer {token}"})

    # Assert
    assert response.status_code == 200
    assert response.json()["tenant_id"] == "org-1"
    assert response.json()["user_id"] == "user-1"


def test_middleware_defaults_to_default_tenant_when_no_jwt(client):
    """
    Test: Middleware defaults to "default-tenant" when no JWT provided.

    Given: No Authorization header
    When: Request is made
    Then: request.state.tenant_id should be "default-tenant"
    """
    response = client.get("/test")

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "default-tenant"
    assert response.json()["user_id"] is None


def test_middleware_handles_invalid_jwt_gracefully(client):
    """
    Test: Middleware handles invalid JWT gracefully (no crash).

    Given: An invalid/malformed JWT token
    When: Request is made with this token
    Then: Middleware should default to "default-tenant" and not crash
    """
    # Make request with invalid token
    response = client.get("/test", headers={"Authorization": "Bearer invalid.token.here"})

    # Assert
    assert response.status_code == 200
    assert response.json()["tenant_id"] == "default-tenant"
    assert response.json()["user_id"] is None


def test_middleware_defaults_when_tenant_id_missing_from_jwt(client):
    """
    Test: Middleware defaults to "default-tenant" when tenant_id claim is missing.

    Given: A valid JWT token without tenant_id claim (create_access_token adds default)
    When: Request is made with this token
    Then: request.state.tenant_id should be "contexia-org-1" (added by create_access_token)
    """
    # Create token without tenant_id (create_access_token adds contexia-org-1)
    token = create_access_token({"sub": "user-2", "email": "user2@example.com"})

    # Make request
    response = client.get("/test", headers={"Authorization": f"Bearer {token}"})

    # Assert
    assert response.status_code == 200
    assert response.json()["tenant_id"] == "contexia-org-1"
    assert response.json()["user_id"] == "user-2"


def test_middleware_extracts_contexia_org_tenant(client):
    """
    Test: Middleware correctly extracts tenant_id for Contexia org.

    Given: A JWT token with tenant_id = "contexia-org-1" (real production tenant)
    When: Request is made with this token
    Then: request.state.tenant_id should be "contexia-org-1"
    """
    token = create_access_token(
        {"sub": "juan@contexia.local", "tenant_id": "contexia-org-1"}
    )

    response = client.get("/test", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "contexia-org-1"


def test_middleware_extracts_client_tenant(client):
    """
    Test: Middleware correctly extracts tenant_id for client org.

    Given: A JWT token with tenant_id = "client-xyz" (client org)
    When: Request is made with this token
    Then: request.state.tenant_id should be "client-xyz"
    """
    token = create_access_token(
        {"sub": "user@client-xyz.local", "tenant_id": "client-xyz"}
    )

    response = client.get("/test", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "client-xyz"
