from supabase import create_client, Client
from config import settings


class LazySupabaseClient:
    """Lazy-load Supabase client on first access, not at import time."""

    def __init__(self, key_attr: str = "SUPABASE_KEY"):
        self._client: Client | None = None
        self._key_attr = key_attr

    def _ensure_initialized(self) -> Client:
        if self._client is None:
            key = getattr(settings, self._key_attr)
            self._client = create_client(settings.SUPABASE_URL, key)
        return self._client

    def __getattr__(self, name):
        return getattr(self._ensure_initialized(), name)


# Default client (anon key) — used by everything except governance operations.
supabase_client = LazySupabaseClient()

# Service-role client — bypasses RLS in a controlled way for governance
# operations only (agent access-control reads + agent_operations audit writes).
# Built from SUPABASE_SERVICE_ROLE_KEY. Never expose to request input.
# See change agent-operations-multitenant-security, design D6.
service_supabase_client = LazySupabaseClient(key_attr="SUPABASE_SERVICE_ROLE_KEY")
