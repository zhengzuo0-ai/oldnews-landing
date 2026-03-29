"""OldNews Backend — FastAPI app with all endpoints."""

import logging
import os
import uuid
from datetime import date, datetime

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from config import API_SECRET, BASE_URL, RESEND_API_KEY, RESEND_FROM_EMAIL
from daily_page import generate_daily_page, generate_verification_page
from database import supabase
from email_templates import verification_email_html
from models import StoryCreate, SubscribeRequest, WatchRequest
from pipeline import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OldNews API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Daily Scheduler ──────────────────────────────────────────────────
scheduler = AsyncIOScheduler()

PIPELINE_HOUR = int(os.environ.get("PIPELINE_HOUR", "8"))
PIPELINE_MINUTE = int(os.environ.get("PIPELINE_MINUTE", "0"))
PIPELINE_TIMEZONE = os.environ.get("PIPELINE_TIMEZONE", "UTC")


async def scheduled_pipeline():
    """Wrapper for the scheduled daily pipeline run."""
    logger.info("Scheduled pipeline starting...")
    try:
        result = await run_pipeline()
        logger.info(f"Scheduled pipeline completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled pipeline failed: {e}")


@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(
        scheduled_pipeline,
        CronTrigger(hour=PIPELINE_HOUR, minute=PIPELINE_MINUTE, timezone=PIPELINE_TIMEZONE),
        id="daily_pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — daily pipeline at {PIPELINE_HOUR:02d}:{PIPELINE_MINUTE:02d} {PIPELINE_TIMEZONE}")

    # Check if today's pipeline has already run (handles container restarts)
    if os.environ.get("PIPELINE_CATCHUP", "true").lower() == "true":
        try:
            today = date.today().isoformat()
            run_check = supabase.table("pipeline_runs").select("id").eq("run_date", today).execute()
            if not run_check.data:
                now = datetime.utcnow()
                scheduled_time = now.replace(hour=PIPELINE_HOUR, minute=PIPELINE_MINUTE, second=0)
                if now > scheduled_time:
                    logger.info("Pipeline missed today — running catch-up")
                    import asyncio
                    asyncio.create_task(scheduled_pipeline())
        except Exception as e:
            logger.warning(f"Catch-up check failed: {e}")


@app.on_event("shutdown")
async def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


# ── Health ────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    from config import SUPABASE_URL, SERPER_API_KEY, MINIMAX_API_KEY
    checks = {
        "supabase": bool(SUPABASE_URL) and supabase is not None,
        "serper_key": bool(SERPER_API_KEY),
        "ai_key": bool(MINIMAX_API_KEY),
        "resend_key": bool(RESEND_API_KEY),
    }
    all_ok = all(checks.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
    }


@app.get("/health/pipeline")
async def pipeline_health():
    """Check if today's pipeline ran successfully. For external monitoring."""
    today = date.today().isoformat()
    now = datetime.utcnow()
    expected_by = now.replace(hour=PIPELINE_HOUR + 1, minute=0, second=0)

    try:
        run_resp = supabase.table("pipeline_runs").select("*").eq("run_date", today).execute()
        if run_resp.data:
            run = run_resp.data[0]
            return {"status": "ok" if run["status"] == "success" else "degraded", "run": run}
        elif now > expected_by:
            return {"status": "missed", "message": f"No pipeline run found for {today} (expected by {PIPELINE_HOUR+1}:00 UTC)"}
        else:
            return {"status": "pending", "message": f"Pipeline scheduled for {PIPELINE_HOUR:02d}:00 UTC"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Stories ───────────────────────────────────────────────────────────


@app.post("/api/stories")
async def create_story(story: StoryCreate, x_api_secret: str = Header(None, alias="X-API-Secret")):
    if API_SECRET and x_api_secret != API_SECRET:
        raise HTTPException(status_code=403, detail="Invalid API secret")
    data = (
        supabase.table("stories")
        .insert(
            {
                "title": story.title,
                "summary": story.summary,
                "category": story.category,
                "current_status": story.current_status,
                "source": story.source,
            }
        )
        .execute()
    )
    return data.data[0]


@app.get("/api/stories")
async def list_stories():
    data = (
        supabase.table("stories")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .execute()
    )
    return data.data


@app.patch("/api/stories/{story_id}/deactivate")
async def deactivate_story(story_id: str, x_api_secret: str = Header(None, alias="X-API-Secret")):
    if API_SECRET and x_api_secret != API_SECRET:
        raise HTTPException(status_code=403, detail="Invalid API secret")
    data = (
        supabase.table("stories")
        .update({"is_active": False})
        .eq("id", story_id)
        .execute()
    )
    if not data.data:
        raise HTTPException(status_code=404, detail="Story not found")
    return {"status": "deactivated", "story_id": story_id}


@app.get("/api/stories/{story_id}/updates")
async def story_updates(story_id: str):
    data = (
        supabase.table("updates")
        .select("*")
        .eq("story_id", story_id)
        .order("created_at", desc=True)
        .execute()
    )
    return data.data


# ── Subscribe + Verify ────────────────────────────────────────────────


@app.post("/api/subscribe")
async def subscribe(req: SubscribeRequest):
    # Check if user already exists
    existing = (
        supabase.table("users").select("*").eq("email", req.email).execute()
    )

    if existing.data:
        user = existing.data[0]
        if user.get("verified"):
            raise HTTPException(status_code=400, detail="Email already verified")
    else:
        # Create new user
        user_token = str(uuid.uuid4())
        verification_token = str(uuid.uuid4())
        user_data = (
            supabase.table("users")
            .insert(
                {
                    "email": req.email,
                    "lang": req.lang,
                    "token": user_token,
                    "verified": False,
                    "verification_token": verification_token,
                }
            )
            .execute()
        )
        user = user_data.data[0]

    # Create watches for selected stories
    for story_id in req.story_ids:
        try:
            supabase.table("watches").insert(
                {"user_id": user["id"], "story_id": story_id}
            ).execute()
        except Exception:
            pass  # Ignore duplicate watches

    # Get watched stories for the verification email
    watched = []
    for sid in req.story_ids:
        s = supabase.table("stories").select("*").eq("id", sid).execute()
        if s.data:
            watched.append(s.data[0])

    # Send verification email
    verify_url = f"{BASE_URL}/api/verify?token={user['verification_token']}"
    html = verification_email_html(verify_url, watched, req.lang)
    subject = (
        "👀 确认你的邮箱 — 旧闻"
        if req.lang == "cn"
        else "👀 Confirm your email — OldNews"
    )

    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": RESEND_FROM_EMAIL,
                "to": req.email,
                "subject": subject,
                "html": html,
            },
            timeout=10.0,
        )

    return {"success": True, "message": "Verification email sent"}


@app.get("/api/verify", response_class=HTMLResponse)
async def verify_email(token: str):
    # Find user by verification token
    result = (
        supabase.table("users")
        .select("*")
        .eq("verification_token", token)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Invalid verification token")

    user = result.data[0]

    # Mark as verified
    supabase.table("users").update({"verified": True}).eq(
        "id", user["id"]
    ).execute()

    # Get user's watched stories
    watches = (
        supabase.table("watches")
        .select("story_id")
        .eq("user_id", user["id"])
        .execute()
    )
    watched_ids = [w["story_id"] for w in watches.data]
    watched_stories = []
    for sid in watched_ids:
        s = supabase.table("stories").select("*").eq("id", sid).execute()
        if s.data:
            watched_stories.append(s.data[0])

    # Get 10 more stories (not already watched)
    all_stories = (
        supabase.table("stories")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    new_stories = [s for s in all_stories.data if s["id"] not in watched_ids][:10]

    lang = user.get("lang", "en")
    html = generate_verification_page(
        user, watched_stories, new_stories, BASE_URL, lang
    )
    return HTMLResponse(content=html)


# ── Watch ─────────────────────────────────────────────────────────────


@app.post("/api/watch")
async def watch_story(req: WatchRequest):
    # Find user by permanent token
    result = (
        supabase.table("users").select("*").eq("token", req.token).execute()
    )
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = result.data[0]

    # Add watch (ignore if already exists)
    try:
        supabase.table("watches").insert(
            {"user_id": user["id"], "story_id": req.story_id}
        ).execute()
    except Exception:
        pass

    return {"success": True}


# ── Daily Page ────────────────────────────────────────────────────────


@app.get("/daily/{date_str}", response_class=HTMLResponse)
async def daily_page(date_str: str, token: str):
    # Find user by permanent token
    result = (
        supabase.table("users").select("*").eq("token", token).execute()
    )
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = result.data[0]
    lang = user.get("lang", "en")

    # Get user's watched stories
    watches = (
        supabase.table("watches")
        .select("story_id")
        .eq("user_id", user["id"])
        .execute()
    )
    watched_ids = [w["story_id"] for w in watches.data]

    # Get watched stories with today's updates
    watched_stories = []
    for sid in watched_ids:
        story = supabase.table("stories").select("*").eq("id", sid).execute()
        if not story.data:
            continue
        s = story.data[0]

        # Check for updates on this date
        updates = (
            supabase.table("updates")
            .select("*")
            .eq("story_id", sid)
            .gte("created_at", f"{date_str}T00:00:00")
            .lte("created_at", f"{date_str}T23:59:59")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        s["update"] = updates.data[0] if updates.data else None
        watched_stories.append(s)

    # Get 10 new stories not in watchlist
    all_stories = (
        supabase.table("stories")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    new_stories = [s for s in all_stories.data if s["id"] not in watched_ids][:10]

    html = generate_daily_page(
        date_str, user, watched_stories, new_stories, BASE_URL, lang
    )
    return HTMLResponse(content=html)


# ── Pipeline ──────────────────────────────────────────────────────────


@app.post("/api/pipeline/run")
async def trigger_pipeline(x_api_secret: str = Header(None, alias="X-API-Secret")):
    if API_SECRET and x_api_secret != API_SECRET:
        raise HTTPException(status_code=403, detail="Invalid API secret")
    start = datetime.utcnow()
    try:
        result = await run_pipeline()
        result["duration_seconds"] = (datetime.utcnow() - start).total_seconds()
        result["status"] = "success"
        result["timestamp"] = start.isoformat()
        logger.info(f"Pipeline completed: {result}")
        return result
    except Exception as e:
        duration = (datetime.utcnow() - start).total_seconds()
        logger.error(f"Pipeline failed after {duration}s: {e}")
        # Log failure to database
        try:
            supabase.table("pipeline_runs").upsert(
                {
                    "run_date": date.today().isoformat(),
                    "status": "failed",
                    "duration_seconds": duration,
                    "error_message": str(e)[:500],
                },
                on_conflict="run_date",
            ).execute()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


@app.get("/api/pipeline/history")
async def pipeline_history(x_api_secret: str = Header(None, alias="X-API-Secret")):
    if API_SECRET and x_api_secret != API_SECRET:
        raise HTTPException(status_code=403, detail="Invalid API secret")
    data = (
        supabase.table("pipeline_runs")
        .select("*")
        .order("run_date", desc=True)
        .limit(30)
        .execute()
    )
    return data.data


# ── Stats ─────────────────────────────────────────────────────────────


@app.get("/api/stats")
async def stats():
    stories = (
        supabase.table("stories")
        .select("id", count="exact")
        .eq("is_active", True)
        .execute()
    )
    users = (
        supabase.table("users")
        .select("id", count="exact")
        .eq("verified", True)
        .execute()
    )
    today = date.today().isoformat()
    updates = (
        supabase.table("updates")
        .select("id", count="exact")
        .gte("created_at", f"{today}T00:00:00")
        .execute()
    )
    # Get today's pipeline run status
    pipeline_run = None
    try:
        run_resp = (
            supabase.table("pipeline_runs")
            .select("*")
            .eq("run_date", today)
            .execute()
        )
        if run_resp.data:
            pipeline_run = run_resp.data[0]
    except Exception:
        pass

    return {
        "active_stories": stories.count,
        "verified_users": users.count,
        "updates_today": updates.count,
        "pipeline_today": pipeline_run,
    }
