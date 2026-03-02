import os

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "OldNews <hello@oldnews.io>")
SERPER_API_KEY = os.environ["SERPER_API_KEY"]
MINIMAX_API_KEY = os.environ["MINIMAX_API_KEY"]
BASE_URL = os.environ.get("BASE_URL", "https://oldnews.io")
API_SECRET = os.environ.get("API_SECRET", "")
