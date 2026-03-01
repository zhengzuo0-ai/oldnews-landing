# OldNews (旧闻) — Project Context

## What is OldNews

OldNews is a news follow-up tracking product. Core insight: news stories dominate headlines for a few days then disappear, but the underlying events keep developing. OldNews watches stories for users and notifies them only when something actually changes.

Brand tagline (EN): "The news gets old. The story keeps going."
Brand tagline (CN): "新闻在变旧，事情仍然在发展。"
Chinese brand name: 旧闻

## Current State

The landing page is built and being deployed to Vercel. The repo is at:
https://github.com/zhengzuo0-ai/oldnews-landing

Domain: oldnews.io (registering on GoDaddy)
Deployment: Vercel (static site + serverless function)
Email collection: Resend API

### File Structure
```
oldnews-landing/
├── public/
│   ├── index.html          # English landing page (default at /)
│   └── cn.html             # Chinese landing page (at /cn)
├── api/
│   └── subscribe.js        # Vercel Serverless Function — collects email via Resend
├── vercel.json             # Route config: / → index.html, /cn → cn.html
└── README.md               # Deployment guide
```

## Product Architecture (To Build)

### Overview
Daily pipeline: curate stories → track with AI → email users updates

### Tech Stack
- Backend: Python FastAPI (integrates with existing OpenClaw automation framework)
- Database: Supabase (PostgreSQL, free tier)
- Search: Serper API (Google search, $50/mo for 10k queries)
- AI: Claude API (Sonnet for progress judgment, ~$0.003 per call)
- Email: Resend API (free tier, 3000 contacts)
- Hosting: Railway or Fly.io for backend; Vercel for frontend

### Database Schema (Supabase)

**stories**
- id (uuid, primary key)
- title (text)
- summary (text)
- category (text) — e.g. "Litigation · Aviation"
- current_status (text) — one-sentence state summary for AI comparison
- source (text)
- created_at (timestamp)
- last_updated (timestamp)
- is_active (boolean, default true)

**users**
- id (uuid, primary key)
- email (text, unique)
- lang (text) — "en" or "cn"
- created_at (timestamp)

**watches**
- id (uuid, primary key)
- user_id (uuid, foreign key → users)
- story_id (uuid, foreign key → stories)
- created_at (timestamp)

**updates**
- id (uuid, primary key)
- story_id (uuid, foreign key → stories)
- level (text) — "big_move" or "small_move"
- summary (text) — 2-3 sentence description of what changed
- new_status (text) — updated state summary
- created_at (timestamp)

### Daily Pipeline (cron job, runs every morning)

**Step 1: Search for new info**
For each active story, use Serper API to search for latest news.
Query: story title + key entities, filtered to last 24 hours.

**Step 2: AI judgment**
For each story with search results, call Claude API:

```
You are a news progress detector.

Story: {title}
Last known status ({last_updated}): {current_status}
New information found today: {search_results}

Determine:
1. Is there substantive new progress compared to last status? (yes/no)
2. If yes, level: big_move (ruling, acquisition, policy change) or small_move (new info but not decisive)
3. 2-3 sentence summary of what changed.
4. Updated status summary (one sentence, for next comparison).

Respond in JSON:
{"has_progress": bool, "level": "big_move"|"small_move"|null, "summary": "...", "new_status": "..."}
```

**Step 3: Update database**
If has_progress is true, insert into updates table and update story's current_status.

**Step 4: Send emails**
For each user, find their watched stories that have updates today.
Compose email using Resend API with the update summaries.
If no updates for a user's stories, either skip or send "nothing changed today."

### Email Format
- Subject line: "旧闻 3.1 | 波音的事又有动静了" or "OldNews 3.1 | Boeing case moves forward"
- Body: story cards with level badges (🔴 Big move, 🟡 Small move)
- Each card: category, title, 2-3 sentence summary, days tracked
- Footer: link to manage preferences, unsubscribe

### Telegram Bot Integration (via OpenClaw)
- `/add_story` — add a new story to track (manual curation)
- `/run_update` — manually trigger the daily pipeline
- `/stats` — show subscriber count, active stories, today's updates

## Design System

### Color Palette (Scheme 7: Dark Slate + Gold)
- Slate: #2a3a40 (hero bg, header, footer)
- Gold: #b8956a (accents, CTAs, highlights)
- Cream: #f5f0ea (content background)
- Card: #fff with #e4ddd0 border
- Text dark: #2a3a40
- Text mid: #6a7a7e
- Text light: #8a9a9e
- Red (big move): #c4453a

### Fonts
- English: Fraunces (serif, headlines), DM Sans (sans, body)
- Chinese: Noto Serif SC (headlines), DM Sans (body)

### UI Patterns
- Button: "Watch this" → "👀 Watching" (EN), "帮我盯着" → "👀 盯着了" (CN)
- Timeline labels: Big move / Small move / Story begins (EN), 大动静 / 小动静 / 事件发生 (CN)
- How it works: Pick · Watch · Know (EN), 选 · 盯 · 收 (CN)

## Key Product Decisions

1. **Daily email, not app.** Habit formation like Morning Brew. Variable length based on actual updates.
2. **Manual story curation at first.** Zee picks 10 stories daily. Automate later.
3. **AI judges progress, not keywords.** State comparison, not keyword matching. This is the core differentiator vs Google Alerts.
4. **Show, don't tell.** Timeline on landing page demonstrates value without explaining it.
5. **Two languages, not a translation.** EN is primary, CN is localized. Same product, different voice.
6. **"盯" (watch) is the core verb.** Used consistently across both languages in all UI elements.

## Who Is Building This

Zee (CEO of Paramount Matter Holdings) is building OldNews as a side project.
Existing infra: OpenClaw automation framework with Telegram bots, FastAPI backends, Claude API integrations.
The backend should integrate with OpenClaw's existing patterns.

## Immediate Next Steps

1. Finish Vercel deployment + Resend integration (landing page live)
2. Register oldnews.io on GoDaddy, configure DNS
3. Build backend pipeline with OpenClaw (FastAPI + Supabase + Claude API + Serper + Resend)
4. Start collecting emails, manually curate 10 stories/day
5. Ship first email to subscribers within 2 weeks
