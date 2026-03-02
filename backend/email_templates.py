"""OldNews email templates — verification and daily update emails.

All emails use inline CSS and system fonts.
Color scheme: slate #2a3a40, gold #b8956a, cream #f5f0ea, red #c4453a.
"""

from datetime import datetime


def _base_wrapper(content: str) -> str:
    """Wrap email content in the base layout."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f0ea;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0ea;">
<tr><td align="center" style="padding:24px 16px;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;">

<!-- Header -->
<tr><td style="background:#2a3a40;padding:20px 24px;border-radius:10px 10px 0 0;">
<span style="font-family:Georgia,serif;font-size:22px;font-weight:bold;color:#e8e0d4;">old<span style="color:#b8956a;">news</span></span>
</td></tr>

<!-- Body -->
<tr><td style="background:#ffffff;padding:32px 24px;border-left:1px solid #e4ddd0;border-right:1px solid #e4ddd0;">
{content}
</td></tr>

<!-- Footer -->
<tr><td style="background:#2a3a40;padding:20px 24px;border-radius:0 0 10px 10px;text-align:center;">
<span style="font-family:Georgia,serif;font-size:14px;color:#e8e0d4;">old<span style="color:#b8956a;">news</span></span>
<br><span style="font-size:11px;color:#8a9a9e;">The news gets old. The story keeps going.</span>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def _story_card_email(story: dict, show_badge: bool = False, level: str = None, summary: str = None) -> str:
    """Render a story card for emails."""
    badge = ""
    if show_badge and level:
        if level == "big_move":
            badge = '<span style="display:inline-block;font-size:10px;font-weight:bold;letter-spacing:1px;padding:2px 8px;border-radius:3px;background:rgba(196,69,58,0.1);color:#c4453a;margin-bottom:6px;">🔴 BIG MOVE</span><br>'
        else:
            badge = '<span style="display:inline-block;font-size:10px;font-weight:bold;letter-spacing:1px;padding:2px 8px;border-radius:3px;background:rgba(184,149,106,0.08);color:#b8956a;margin-bottom:6px;">🟡 SMALL MOVE</span><br>'

    summary_html = ""
    if summary:
        summary_html = f'<p style="font-size:13px;color:#6a7a7e;line-height:1.6;margin:8px 0 0;">{summary}</p>'

    return f"""<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
<tr><td style="background:#fff;border:1px solid #e4ddd0;border-radius:8px;padding:16px 18px;">
{badge}
<span style="font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:#b8956a;">{story.get("category", "")}</span>
<p style="font-family:Georgia,serif;font-size:15px;font-weight:500;color:#2a3a40;line-height:1.35;margin:4px 0 0;">{story.get("title", "")}</p>
{summary_html}
<p style="font-size:11px;color:#8a9a9e;margin:6px 0 0;">{story.get("source", "")}</p>
</td></tr>
</table>"""


def _story_brief_email(story: dict) -> str:
    """Render a brief story entry for the 'more stories' section."""
    return f"""<tr><td style="padding:10px 0;border-bottom:1px solid #f0ebe4;">
<span style="font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:#b8956a;">{story.get("category", "")}</span>
<p style="font-family:Georgia,serif;font-size:14px;color:#2a3a40;margin:3px 0 0;line-height:1.3;">{story.get("title", "")}</p>
<p style="font-size:12px;color:#6a7a7e;margin:3px 0 0;line-height:1.5;">{story.get("summary", "")[:120]}...</p>
</td></tr>"""


def verification_email_html(verify_url: str, stories: list[dict], lang: str = "en") -> str:
    """Generate verification email HTML."""
    if lang == "cn":
        heading = "确认你的邮箱"
        intro = "点击下面的按钮确认你的邮箱，开始接收旧闻的每日更新。"
        btn_text = "确认邮箱"
        watching_label = "👀 你选了这些新闻"
        note = "确认后，你明天早上就会收到第一封邮件。"
    else:
        heading = "Confirm your email"
        intro = "Click the button below to confirm your email and start receiving daily updates from OldNews."
        btn_text = "Confirm email"
        watching_label = "👀 You picked these stories"
        note = "Once confirmed, you'll get your first email tomorrow morning."

    stories_html = ""
    if stories:
        cards = "".join(_story_card_email(s) for s in stories)
        stories_html = f"""
<p style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#b8956a;margin:24px 0 12px;">{watching_label}</p>
{cards}"""

    content = f"""
<h2 style="font-family:Georgia,serif;font-size:22px;font-weight:500;color:#2a3a40;margin:0 0 12px;">{heading}</h2>
<p style="font-size:14px;color:#6a7a7e;line-height:1.6;margin:0 0 24px;">{intro}</p>

<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center">
<a href="{verify_url}" style="display:inline-block;padding:14px 36px;background:#b8956a;color:#2a3a40;font-size:14px;font-weight:bold;text-decoration:none;border-radius:6px;">{btn_text}</a>
</td></tr>
</table>

{stories_html}

<p style="font-size:12px;color:#8a9a9e;margin:20px 0 0;text-align:center;">{note}</p>
"""
    return _base_wrapper(content)


def daily_email_subject(date_str: str, updates: list[dict], lang: str = "en") -> str:
    """Generate the daily email subject line."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_short = f"{dt.month}.{dt.day}"
    except ValueError:
        date_short = date_str

    if not updates:
        if lang == "cn":
            return f"旧闻 {date_short} | 今天没有大动静"
        return f"OldNews {date_short} | Quiet day for your stories"

    # Use the first big_move, or first update
    lead = None
    for u in updates:
        if u.get("level") == "big_move":
            lead = u
            break
    if not lead:
        lead = updates[0]

    title = lead.get("story", {}).get("title", "")
    # Truncate title for subject
    if len(title) > 40:
        title = title[:37] + "..."

    if lang == "cn":
        return f"旧闻 {date_short} | {title}"
    return f"OldNews {date_short} | {title}"


def daily_email_html(
    date_str: str,
    watched_updates: list[dict],
    new_stories: list[dict],
    daily_url: str,
    lang: str = "en",
) -> str:
    """Generate the daily update email HTML."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if lang == "cn":
            date_display = f"{dt.year}年{dt.month}月{dt.day}日"
        else:
            date_display = dt.strftime("%B %d, %Y")
    except ValueError:
        date_display = date_str

    if lang == "cn":
        updates_label = "你盯着的新闻有动静了"
        more_label = "更多新闻"
        view_all = "在每日页面查看全部 →"
        no_updates = "你盯着的新闻今天没有新进展。"
    else:
        updates_label = "Your stories moved"
        more_label = "10 More Stories"
        view_all = "View all on your daily page →"
        no_updates = "No updates on your watched stories today."

    # Updates section
    if watched_updates:
        update_cards = "".join(
            _story_card_email(
                u["story"],
                show_badge=True,
                level=u.get("level"),
                summary=u.get("summary"),
            )
            for u in watched_updates
        )
        updates_section = f"""
<p style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#b8956a;margin:0 0 12px;">{updates_label}</p>
{update_cards}"""
    else:
        updates_section = f'<p style="font-size:14px;color:#8a9a9e;margin:0 0 16px;">{no_updates}</p>'

    # New stories section
    new_stories_rows = "".join(_story_brief_email(s) for s in new_stories[:10])
    new_section = ""
    if new_stories:
        new_section = f"""
<p style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#b8956a;margin:28px 0 12px;">{more_label}</p>
<table width="100%" cellpadding="0" cellspacing="0">
{new_stories_rows}
</table>"""

    content = f"""
<p style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#8a9a9e;margin:0 0 20px;">{date_display}</p>

{updates_section}

{new_section}

<table width="100%" cellpadding="0" cellspacing="0" style="margin:28px 0 0;">
<tr><td align="center">
<a href="{daily_url}" style="display:inline-block;padding:12px 32px;background:#b8956a;color:#2a3a40;font-size:13px;font-weight:bold;text-decoration:none;border-radius:6px;">{view_all}</a>
</td></tr>
</table>

<p style="font-size:11px;color:#8a9a9e;text-align:center;margin:24px 0 0;">
<a href="{daily_url}" style="color:#8a9a9e;">{"退订" if lang == "cn" else "Unsubscribe"}</a>
</p>
"""
    return _base_wrapper(content)
