"""Supabase client accessors for antigravity-app.

Unified on the single lazy clients defined in ``infrastructure.supabase_client``
so the whole backend shares one underlying connection and one config source.
"""

from infrastructure.supabase_client import supabase_client, service_supabase_client


def get_supabase():
    """Return the shared lazy Supabase client (anon key, initialized on first use)."""
    return supabase_client


def get_service_supabase():
    """Return the shared lazy service-role Supabase client.

    Bypasses RLS in a controlled way for governance operations only
    (agent access-control reads of user_tenants/user_roles and agent_operations
    audit writes). Never expose this client to request-controlled input.
    See change agent-operations-multitenant-security, design D6.
    """
    return service_supabase_client
