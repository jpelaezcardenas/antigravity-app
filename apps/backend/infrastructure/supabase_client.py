from supabase import create_client, Client
from config import settings


class LazySupabaseClient:
    """Lazy-load Supabase client on first access, not at import time."""

    def __init__(self):
        self._client: Client | None = None

    def _ensure_initialized(self) -> Client:
        if self._client is None:
            self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return self._client

    def __getattr__(self, name):
        return getattr(self._ensure_initialized(), name)


supabase_client = LazySupabaseClient()
