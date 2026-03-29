"""OldNews daily pipeline: search → AI judge → update DB → send emails."""

import asyncio
import json
import logging
import os
from datetime import date, datetime

import httpx


async def retry_async(func, max_retries=3, backoff=2):
    """Retry an async function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = backoff ** attempt
            logging.getLogger(__name__).warning(
                f"Retry {attempt + 1}/{max_retries} after {wait}s: {e}"
            )
            await asyncio.sleep(wait)

from config import (
    AI_MODEL,
    AI_TIMEOUT,
    BASE_URL,
    EMAIL_TIMEOUT,
    MINIMAX_API_KEY,
    NEW_STORIES_LIMIT,
    RESEND_API_KEY,
    RESEND_FROM_EMAIL,
    SEARCH_RESULTS_LIMIT,
    SEARCH_TIMEOUT,
    SERPER_API_KEY,
)
from database import supabase
from email_templates import daily_email_html, daily_email_subject

logger = logging.getLogger(__name__)


async def search_story(client: httpx.AsyncClient, title: str) -> list[dict]:
    """Search for latest news about a story using Serper API (last 24h)."""
    response = await client.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": title, "num": SEARCH_RESULTS_LIMIT, "tbs": "qdr:d"},
        timeout=SEARCH_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("organic", [])


async def judge_progress(
    client: httpx.AsyncClient, story: dict, search_results: list[dict]
) -> dict:
    """Use Claude to judge if there's real progress on a story."""
    results_text = "\n".join(
        f"- {r.get('title', '')}: {r.get('snippet', '')}"
        for r in search_results[:5]
    )

    prompt = f"""You are a news progress detector.

Story: {story['title']}
Last known status ({story['last_updated']}): {story['current_status']}
New information found today:
{results_text}

Determine:
1. Is there substantive new progress compared to last status? (yes/no)
2. If yes, level: big_move (ruling, acquisition, policy change) or small_move (new info but not decisive)
3. 2-3 sentence summary of what changed.
4. Updated status summary (one sentence, for next comparison).

Respond in JSON only:
{{"has_progress": true/false, "level": "big_move" or "small_move" or null, "summary": "...", "new_status": "..."}}"""

    response = await client.post(
        "https://api.minimaxi.chat/v1/text/chatcompletion_v2",
        headers={
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": AI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0.1,
        },
        timeout=AI_TIMEOUT,
    )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]

    # Extract JSON from response
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    return {"has_progress": False, "level": None, "summary": "", "new_status": ""}


async def run_pipeline() -> dict:
    """Run the full daily pipeline: search → judge → update DB → send emails."""
    stats = {"stories_checked": 0, "updates_found": 0, "emails_sent": 0, "emails_failed": 0, "skipped_duplicate": 0, "errors": 0}
    today = date.today().isoformat()

    # Get all active stories
    stories_resp = (
        supabase.table("stories").select("*").eq("is_active", True).execute()
    )
    stories = stories_resp.data
    stats["stories_checked"] = len(stories)

    # Get today's existing updates to prevent duplicates
    existing_updates_resp = (
        supabase.table("updates")
        .select("story_id")
        .gte("created_at", f"{today}T00:00:00")
        .execute()
    )
    already_updated_ids = {u["story_id"] for u in existing_updates_resp.data}

    if not stories:
        logger.info("No active stories to check")
        return stats

    updates_today = []

    async with httpx.AsyncClient() as client:
        # Step 1 & 2: Search and judge each story
        for story in stories:
            try:
                # Skip stories already updated today (idempotency)
                if story["id"] in already_updated_ids:
                    stats["skipped_duplicate"] += 1
                    logger.info(f"Skipping (already updated today): {story['title']}")
                    continue

                results = await retry_async(
                    lambda s=story: search_story(client, s["title"]), max_retries=2
                )
                if not results:
                    logger.info(f"No search results for: {story['title']}")
                    continue

                judgment = await retry_async(
                    lambda s=story, r=results: judge_progress(client, s, r), max_retries=2
                )

                if judgment.get("has_progress"):
                    # Step 3: Update database
                    supabase.table("updates").insert(
                        {
                            "story_id": story["id"],
                            "level": judgment["level"],
                            "summary": judgment["summary"],
                            "new_status": judgment["new_status"],
                        }
                    ).execute()

                    supabase.table("stories").update(
                        {
                            "current_status": judgment["new_status"],
                            "last_updated": datetime.utcnow().isoformat(),
                        }
                    ).eq("id", story["id"]).execute()

                    updates_today.append(
                        {
                            "story": story,
                            "level": judgment["level"],
                            "summary": judgment["summary"],
                        }
                    )
                    stats["updates_found"] += 1
                    logger.info(
                        f"Update found for {story['title']}: {judgment['level']}"
                    )

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error processing story {story['title']}: {e}")
                continue

        # Step 4: Send emails to verified users
        users_resp = (
            supabase.table("users").select("*").eq("verified", True).execute()
        )
        users = users_resp.data

        # Get 10 latest stories for the "more stories" section
        new_stories_resp = (
            supabase.table("stories")
            .select("*")
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(NEW_STORIES_LIMIT)
            .execute()
        )
        new_stories_all = new_stories_resp.data

        for user in users:
            try:
                # Get user's watched story IDs
                watches_resp = (
                    supabase.table("watches")
                    .select("story_id")
                    .eq("user_id", user["id"])
                    .execute()
                )
                watched_ids = {w["story_id"] for w in watches_resp.data}

                # Filter updates for this user's watched stories
                user_updates = [
                    u for u in updates_today if u["story"]["id"] in watched_ids
                ]

                # Skip if no updates for this user
                if not user_updates:
                    continue

                daily_url = f"{BASE_URL}/daily/{today}?token={user['token']}"
                lang = user.get("lang", "en")

                # Filter new_stories to exclude already-watched
                extra_stories = [
                    s for s in new_stories_all if s["id"] not in watched_ids
                ][:NEW_STORIES_LIMIT]

                subject = daily_email_subject(today, user_updates, lang)
                html = daily_email_html(
                    today, user_updates, extra_stories, daily_url, lang
                )

                email_resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": RESEND_FROM_EMAIL,
                        "to": user["email"],
                        "subject": subject,
                        "html": html,
                    },
                    timeout=EMAIL_TIMEOUT,
                )
                email_resp.raise_for_status()
                stats["emails_sent"] += 1
                logger.info(f"Email sent to {user['email']}")

            except Exception as e:
                stats["emails_failed"] += 1
                logger.error(f"Error sending email to {user['email']}: {e}")
                continue

    # Log pipeline execution to database
    run_status = "success" if stats["errors"] == 0 else "partial"
    try:
        supabase.table("pipeline_runs").upsert(
            {
                "run_date": today,
                "status": run_status,
                "stories_checked": stats["stories_checked"],
                "updates_found": stats["updates_found"],
                "emails_sent": stats["emails_sent"],
                "skipped_duplicate": stats["skipped_duplicate"],
                "error_message": f"{stats['errors']} stories failed" if stats["errors"] > 0 else None,
            },
            on_conflict="run_date",
        ).execute()
    except Exception as e:
        logger.error(f"Failed to log pipeline run: {e}")

    # Alert admin if there were errors
    admin_email = os.environ.get("ADMIN_EMAIL")
    if admin_email and (stats["errors"] > 0 or stats["emails_failed"] > 0):
        try:
            async with httpx.AsyncClient() as alert_client:
                await alert_client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "from": RESEND_FROM_EMAIL,
                        "to": admin_email,
                        "subject": f"⚠️ OldNews pipeline: {stats['errors']} errors on {today}",
                        "html": f"<p>Pipeline ran with errors.</p><pre>{json.dumps(stats, indent=2)}</pre>",
                    },
                    timeout=EMAIL_TIMEOUT,
                )
        except Exception as e:
            logger.error(f"Failed to send admin alert: {e}")

    logger.info(f"Pipeline complete: {stats}")
    return stats
