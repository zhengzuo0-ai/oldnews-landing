import os
import logging

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "OldNews <hello@oldnews.io>")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
BASE_URL = os.environ.get("BASE_URL", "https://oldnews.io")
API_SECRET = os.environ.get("API_SECRET", "")

# Pipeline configuration
SEARCH_RESULTS_LIMIT = int(os.environ.get("SEARCH_RESULTS_LIMIT", "5"))
AI_MODEL = os.environ.get("AI_MODEL", "MiniMax-M1-80k")
SEARCH_TIMEOUT = float(os.environ.get("SEARCH_TIMEOUT", "15"))
AI_TIMEOUT = float(os.environ.get("AI_TIMEOUT", "30"))
EMAIL_TIMEOUT = float(os.environ.get("EMAIL_TIMEOUT", "10"))
NEW_STORIES_LIMIT = int(os.environ.get("NEW_STORIES_LIMIT", "10"))

# Log missing vars at startup
_required = ["SUPABASE_URL", "SUPABASE_KEY", "SERPER_API_KEY", "MINIMAX_API_KEY", "RESEND_API_KEY"]
_missing = [v for v in _required if not os.environ.get(v)]
if _missing:
    logger.warning(f"Missing environment variables: {_missing}")
