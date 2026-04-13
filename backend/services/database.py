import logging
from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

_client = None


def get_supabase():
    """Get or create Supabase client singleton."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY or "your_" in SUPABASE_URL:
            logger.warning("Supabase not configured — database features disabled")
            return None
        try:
            from supabase import create_client
            _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            logger.error(f"Supabase init error: {e}")
            return None
    return _client


def is_supabase_configured() -> bool:
    return get_supabase() is not None
