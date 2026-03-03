import logging
from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

_supabase = None

def get_supabase():
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
        from supabase import create_client
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized")
    return _supabase

# Backwards compat: lazy property
class _LazySupabase:
    def __getattr__(self, name):
        return getattr(get_supabase(), name)

supabase = _LazySupabase()
