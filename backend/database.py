import logging
from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

supabase = None

try:
    if SUPABASE_URL and SUPABASE_KEY:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    else:
        logger.warning("Supabase credentials not set")
except Exception as e:
    logger.error(f"Failed to initialize Supabase: {e}")
