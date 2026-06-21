"""Supabase client accessor for antigravity-app.

Unified on the single lazy client defined in ``infrastructure.supabase_client``
so the whole backend shares one underlying connection and one config source.
"""

from infrastructure.supabase_client import supabase_client


def get_supabase():
    """Return the shared lazy Supabase client (initialized on first attribute use)."""
    return supabase_client
