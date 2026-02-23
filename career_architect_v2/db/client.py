from supabase import create_client, Client

SUPABASE_URL = "https://clvqqziqhdrfqtgasbat.supabase.co"
SUPABASE_KEY = "sb_publishable_etCObCZdvHfD1qJRWCvbBA_k8jhLN26"

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client
