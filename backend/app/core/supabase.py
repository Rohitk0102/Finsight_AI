from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions
from app.core.config import settings
from functools import lru_cache


def _client_options() -> SyncClientOptions:
    return SyncClientOptions(auto_refresh_token=False, persist_session=False)


@lru_cache
def get_supabase_client() -> Client:
    """Service-role client for all backend DB operations (bypasses RLS)."""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
        options=_client_options(),
    )


# Convenience alias
supabase: Client = get_supabase_client()
