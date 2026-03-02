"""OldNews daily page and verification page HTML generators.

Full responsive pages matching OldNews design system:
- Slate #2a3a40, Gold #b8956a, Cream #f5f0ea, Card white #fff, Red #c4453a
- Fonts: Fraunces (serif), DM Sans (body), Noto Serif SC (CN)
"""

from datetime import datetime


def _page_head(title: str, lang: str = "en") -> str:
    """Generate the <head> section with CSS."""
    lang_attr = "zh" if lang == "cn" else "en"
    return f"""<!DOCTYPE html>
<html lang="{lang_attr}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,500;0,9..144,700;1,9..144,400&family=DM+Sans:wght@400;500;700&family=Noto+Serif+SC:wght@500;700&display=swap" rel="stylesheet">
<style>
:root {{
  --slate: #2a3a40;
  --slate-light: #3a4e56;
  --gold: #b8956a;
  --gold-hover: #a88358;
  --gold-dim: rgba(184,149,106,0.08);
  --cream: #f5f0ea;
  --cream-dark: #ebe4da;
  --card-bg: #fff;
  --card-border: #e4ddd0;
  --text-dark: #2a3a40;
  --text-mid: #6a7a7e;
  --text-light: #8a9a9e;
  --red: #c4453a;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: 'DM Sans', sans-serif;
  background: var(--cream);
  color: var(--text-dark);
  -webkit-font-smoothing: antialiased;
}}
.header {{
  background: var(--slate);
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 50;
}}
.logo {{
  font-family: 'Fraunces', serif;
  font-size: 22px;
  font-weight: 700;
  color: #e8e0d4;
}}
.logo span {{ color: var(--gold); }}
.date-badge {{
  font-size: 12px;
  color: var(--text-light);
  letter-spacing: 1px;
}}
.container {{
  max-width: 660px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}}
.section-label {{
  font-size: 10px;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 16px;
  margin-top: 32px;
}}
.section-label:first-child {{ margin-top: 0; }}

/* Story cards */
.story-card {{
  background: var(--card-bg);
  border: 2px solid var(--card-border);
  border-radius: 10px;
  padding: 18px 20px;
  margin-bottom: 10px;
}}
.story-card.has-update {{ border-color: var(--gold); }}
.badge {{
  display: inline-block;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 2px 8px;
  border-radius: 3px;
  margin-bottom: 6px;
}}
.badge.big {{ background: rgba(196,69,58,0.1); color: var(--red); }}
.badge.small {{ background: var(--gold-dim); color: var(--gold); }}
.badge.none {{ background: rgba(138,154,158,0.1); color: var(--text-light); }}
.story-cat {{
  font-size: 9px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 4px;
}}
.story-title {{
  font-family: {{"'Noto Serif SC'," if lang == "cn" else ""}} 'Fraunces', serif;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-dark);
  line-height: 1.35;
  margin-bottom: 5px;
}}
.story-summary {{
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-mid);
}}
.story-source {{
  font-size: 11px;
  color: var(--text-light);
  margin-top: 6px;
}}
.story-meta {{
  font-size: 11px;
  color: var(--text-light);
  margin-top: 6px;
}}

/* Watch button */
.watch-btn {{
  display: inline-block;
  padding: 8px 16px;
  background: transparent;
  color: var(--text-mid);
  font-family: 'DM Sans', sans-serif;
  font-size: 12px;
  font-weight: 600;
  border: 1.5px solid var(--card-border);
  border-radius: 5px;
  cursor: pointer;
  margin-top: 10px;
  transition: all 0.2s;
}}
.watch-btn:hover {{
  border-color: var(--gold);
  color: var(--slate);
}}
.watch-btn.watched {{
  background: var(--gold);
  color: #fff;
  border-color: var(--gold);
  cursor: default;
}}

/* Welcome banner */
.welcome {{
  background: var(--slate);
  border-radius: 10px;
  padding: 28px 24px;
  text-align: center;
  margin-bottom: 24px;
}}
.welcome h2 {{
  font-family: 'Fraunces', serif;
  font-size: 24px;
  color: #e8e0d4;
  margin-bottom: 8px;
}}
.welcome p {{
  font-size: 14px;
  color: var(--text-light);
  line-height: 1.6;
}}
.welcome .check {{
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--gold);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
  font-size: 24px;
  color: var(--slate);
}}

/* Footer */
.footer {{
  background: var(--slate);
  padding: 24px;
  text-align: center;
  margin-top: 32px;
}}
.footer-logo {{
  font-family: 'Fraunces', serif;
  font-size: 16px;
  color: #e8e0d4;
  margin-bottom: 4px;
}}
.footer-logo span {{ color: var(--gold); }}
.footer p {{ font-size: 11px; color: var(--text-light); }}

/* Responsive */
@media (max-width: 600px) {{
  .header {{ padding: 12px 16px; }}
  .logo {{ font-size: 18px; }}
  .container {{ padding: 16px 12px 36px; }}
  .story-card {{ padding: 14px 16px; }}
  .story-title {{ font-size: 15px; }}
  .welcome {{ padding: 24px 18px; }}
  .welcome h2 {{ font-size: 20px; }}
}}
</style>
</head>"""


def _header(date_display: str) -> str:
    return f"""<div class="header">
  <div class="logo">old<span>news</span></div>
  <div class="date-badge">{date_display}</div>
</div>"""


def _footer(lang: str = "en") -> str:
    tagline = "新闻在变旧，事情仍然在发展。" if lang == "cn" else "The news gets old. The story keeps going."
    return f"""<div class="footer">
  <div class="footer-logo">old<span>news</span></div>
  <p>{tagline}</p>
</div>"""


def _watched_story_card(story: dict, lang: str = "en") -> str:
    """Render a watched story card with optional progress badge."""
    update = story.get("update")
    has_update = update is not None
    card_class = "story-card has-update" if has_update else "story-card"

    if has_update:
        level = update.get("level", "")
        if level == "big_move":
            badge_class = "big"
            badge_text = "🔴 大动静" if lang == "cn" else "🔴 Big move"
        else:
            badge_class = "small"
            badge_text = "🟡 小动静" if lang == "cn" else "🟡 Small move"
        badge_html = f'<div class="badge {badge_class}">{badge_text}</div>'
        summary_html = f'<div class="story-summary">{update.get("summary", "")}</div>'
    else:
        no_change = "暂无变化" if lang == "cn" else "No change"
        badge_html = f'<div class="badge none">{no_change}</div>'
        summary_html = f'<div class="story-summary">{story.get("summary", "")}</div>'

    return f"""<div class="{card_class}">
  {badge_html}
  <div class="story-cat">{story.get("category", "")}</div>
  <div class="story-title">{story.get("title", "")}</div>
  {summary_html}
  <div class="story-source">{story.get("source", "")}</div>
</div>"""


def _new_story_card(story: dict, lang: str = "en") -> str:
    """Render a new story card with a watch button."""
    btn_text = "帮我盯着" if lang == "cn" else "Watch this"
    story_id = story.get("id", "")
    return f"""<div class="story-card" id="card-{story_id}">
  <div class="story-cat">{story.get("category", "")}</div>
  <div class="story-title">{story.get("title", "")}</div>
  <div class="story-summary">{story.get("summary", "")}</div>
  <div class="story-source">{story.get("source", "")}</div>
  <button class="watch-btn" id="btn-{story_id}" onclick="watchStory('{story_id}', this)">{btn_text}</button>
</div>"""


def _watch_js(lang: str = "en") -> str:
    """JavaScript for watch button toggle."""
    watching_text = "👀 盯着了" if lang == "cn" else "👀 Watching"
    error_text = "出错了" if lang == "cn" else "Error"
    return f"""<script>
const token = new URLSearchParams(window.location.search).get('token');

async function watchStory(storyId, btn) {{
  if (btn.classList.contains('watched')) return;
  btn.textContent = '...';
  try {{
    const res = await fetch('/api/watch', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{story_id: storyId, token: token}})
    }});
    if (res.ok) {{
      btn.textContent = '{watching_text}';
      btn.classList.add('watched');
      const card = document.getElementById('card-' + storyId);
      if (card) card.style.borderColor = '#b8956a';
    }} else {{
      btn.textContent = '{error_text}';
      setTimeout(() => btn.textContent = '{"帮我盯着" if lang == "cn" else "Watch this"}', 2000);
    }}
  }} catch (e) {{
    btn.textContent = '{error_text}';
    setTimeout(() => btn.textContent = '{"帮我盯着" if lang == "cn" else "Watch this"}', 2000);
  }}
}}
</script>"""


def generate_daily_page(
    date_str: str,
    user: dict,
    watched_stories: list[dict],
    new_stories: list[dict],
    base_url: str,
    lang: str = "en",
) -> str:
    """Generate the full daily page HTML."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if lang == "cn":
            date_display = f"{dt.year}年{dt.month}月{dt.day}日"
            title = f"旧闻 — {date_display}"
        else:
            date_display = dt.strftime("%B %d, %Y")
            title = f"OldNews — {date_display}"
    except ValueError:
        date_display = date_str
        title = f"OldNews — {date_str}"

    your_stories_label = "你盯着的新闻" if lang == "cn" else "Your stories"
    more_label = "更多新闻" if lang == "cn" else "10 More Stories"

    watched_html = "".join(_watched_story_card(s, lang) for s in watched_stories)
    new_html = "".join(_new_story_card(s, lang) for s in new_stories)

    if not watched_stories:
        no_stories = "你还没有盯着任何新闻。" if lang == "cn" else "You're not watching any stories yet."
        watched_html = f'<p style="color:var(--text-light);font-size:14px;">{no_stories}</p>'

    return f"""{_page_head(title, lang)}
<body>
{_header(date_display)}

<div class="container">
  <div class="section-label">{your_stories_label}</div>
  {watched_html}

  <div class="section-label">{more_label}</div>
  {new_html}
</div>

{_footer(lang)}
{_watch_js(lang)}
</body>
</html>"""


def generate_verification_page(
    user: dict,
    watched_stories: list[dict],
    new_stories: list[dict],
    base_url: str,
    lang: str = "en",
) -> str:
    """Generate the email verification confirmation page HTML."""
    if lang == "cn":
        title = "旧闻 — 邮箱已确认"
        welcome_heading = "邮箱已确认 ✓"
        welcome_text = "你明天早上会收到第一封旧闻邮件。"
        your_label = "你盯着的新闻"
        more_label = "再挑几条？"
    else:
        title = "OldNews — Email Confirmed"
        welcome_heading = "You're verified ✓"
        welcome_text = "You'll get your first OldNews email tomorrow morning."
        your_label = "You're watching"
        more_label = "Pick more stories"

    date_display = datetime.utcnow().strftime("%B %d, %Y")

    watched_html = ""
    for s in watched_stories:
        watched_html += f"""<div class="story-card" style="border-color:var(--gold);background:var(--gold-dim);">
  <div class="story-cat">{s.get("category", "")}</div>
  <div class="story-title">{s.get("title", "")}</div>
  <div class="story-summary">{s.get("summary", "")}</div>
  <div class="story-source">{s.get("source", "")}</div>
  <button class="watch-btn watched">{"👀 盯着了" if lang == "cn" else "👀 Watching"}</button>
</div>"""

    new_html = "".join(_new_story_card(s, lang) for s in new_stories)

    return f"""{_page_head(title, lang)}
<body>
{_header(date_display)}

<div class="container">
  <div class="welcome">
    <div class="check">✓</div>
    <h2>{welcome_heading}</h2>
    <p>{welcome_text}</p>
  </div>

  <div class="section-label">{your_label}</div>
  {watched_html}

  <div class="section-label">{more_label}</div>
  {new_html}
</div>

{_footer(lang)}
{_watch_js(lang)}
</body>
</html>"""
