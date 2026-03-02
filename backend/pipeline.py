"""OldNews daily pipeline: search → AI judge → update DB → send emails."""

import json
import logging
from datetime import date, datetime

import httpx

from config import (
    ANTHROPIC_API_KEY,
    BASE_URL,
    RESEND_API_KEY,
    RESEND_FROM_EMAIL,
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
        json={"q": title, "num": 5, "tbs": "qdr:d"},
        timeout=15.0,
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
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30.0,
    )
    response.raise_for_status()
    text = response.json()["content"][0]["text"]

    # Extract JSON from response
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    return {"has_progress": False, "level": None, "summary": "", "new_status": ""}


async def run_pipeline() -> dict:
    """Run the full daily pipeline: search → judge → update DB → send emails."""
    stats = {"stories_checked": 0, "updates_found": 0, "emails_sent": 0}
    today = date.today().isoformat()

    # Get all active stories
    stories_resp = (
        supabase.table("stories").select("*").eq("is_active", True).execute()
    )
    stories = stories_resp.data
    stats["stories_checked"] = len(stories)

    if not stories:
        logger.info("No active stories to check")
        return stats

    updates_today = []

    async with httpx.AsyncClient() as client:
        # Step 1 & 2: Search and judge each story
        for story in stories:
            try:
                results = await search_story(client, story["title"])
                if not results:
                    logger.info(f"No search results for: {story['title']}")
                    continue

                judgment = await judge_progress(client, story, results)

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
            .limit(10)
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
                ][:10]

                subject = daily_email_subject(today, user_updates, lang)
                html = daily_email_html(
                    today, user_updates, extra_stories, daily_url, lang
                )

                await client.post(
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
                    timeout=10.0,
                )
                stats["emails_sent"] += 1
                logger.info(f"Email sent to {user['email']}")

            except Exception as e:
                logger.error(f"Error sending email to {user['email']}: {e}")
                continue

    logger.info(f"Pipeline complete: {stats}")
    return stats
