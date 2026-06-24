"""
Tests for the Supabase client accessors
(change agent-operations-multitenant-security, Slice 2.0).

Verifies the anon client and the governance service-role client are distinct
and configured from different keys, without initializing real connections.
"""

from __future__ import annotations

from core.supabase_client import get_supabase, get_service_supabase
from infrastructure.supabase_client import supabase_client, service_supabase_client


def test_accessors_return_shared_singletons():
    assert get_supabase() is supabase_client
    assert get_service_supabase() is service_supabase_client


def test_anon_and_service_clients_are_distinct():
    assert get_supabase() is not get_service_supabase()


def test_clients_configured_from_different_keys():
    # Access the private attr directly (no network/init triggered).
    assert supabase_client._key_attr == "SUPABASE_KEY"
    assert service_supabase_client._key_attr == "SUPABASE_SERVICE_ROLE_KEY"
