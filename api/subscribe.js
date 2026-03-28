// Module-level cache for audience ID (persists across warm invocations)
let cachedAudienceId = null;

// Simple in-memory rate limiter (per serverless instance)
const rateLimit = new Map();
const RATE_LIMIT_WINDOW = 60000; // 1 minute
const RATE_LIMIT_MAX = 5; // max 5 requests per IP per minute

function isRateLimited(ip) {
  const now = Date.now();
  const entry = rateLimit.get(ip);
  if (!entry || now - entry.timestamp > RATE_LIMIT_WINDOW) {
    rateLimit.set(ip, { count: 1, timestamp: now });
    return false;
  }
  entry.count++;
  if (entry.count > RATE_LIMIT_MAX) return true;
  return false;
}

async function getOrCreateAudienceId(apiKey) {
  if (cachedAudienceId) return cachedAudienceId;

  // Check env var first
  if (process.env.RESEND_AUDIENCE_ID) {
    cachedAudienceId = process.env.RESEND_AUDIENCE_ID;
    return cachedAudienceId;
  }

  const audienceResponse = await fetch('https://api.resend.com/audiences', {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${apiKey}` },
  });

  if (!audienceResponse.ok) {
    throw new Error(`Failed to fetch audiences: ${audienceResponse.status}`);
  }

  const audiences = await audienceResponse.json();

  if (audiences.data && audiences.data.length > 0) {
    cachedAudienceId = audiences.data[0].id;
  } else {
    const createAudience = await fetch('https://api.resend.com/audiences', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name: 'OldNews Subscribers' }),
    });
    if (!createAudience.ok) {
      throw new Error(`Failed to create audience: ${createAudience.status}`);
    }
    const newAudience = await createAudience.json();
    cachedAudienceId = newAudience.id;
  }

  return cachedAudienceId;
}

export default async function handler(req, res) {
  // CORS - restrict to our domain (allow all in development)
  const allowedOrigins = ['https://oldnews.io', 'https://www.oldnews.io'];
  const origin = req.headers.origin;
  if (allowedOrigins.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
  } else if (origin && origin.endsWith('.vercel.app')) {
    // Allow Vercel preview/staging deployments
    res.setHeader('Access-Control-Allow-Origin', origin);
  } else if (process.env.VERCEL_ENV !== 'production') {
    res.setHeader('Access-Control-Allow-Origin', '*');
  }
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Rate limiting
  const clientIp = req.headers['x-forwarded-for']?.split(',')[0]?.trim() || 'unknown';
  if (isRateLimited(clientIp)) {
    return res.status(429).json({ error: 'Too many requests. Please try again later.' });
  }

  if (!process.env.RESEND_API_KEY) {
    console.error('RESEND_API_KEY is not configured');
    return res.status(500).json({ error: 'Server configuration error' });
  }

  const { email, stories, lang, website } = req.body;

  // Honeypot check - bots fill the hidden "website" field
  if (website) {
    return res.status(200).json({ success: true }); // silent success to not tip off bots
  }

  // Stronger email validation
  if (!email || typeof email !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ error: 'Invalid email' });
  }
  const normalizedEmail = email.toLowerCase().trim();

  // Validate stories is an array if provided, limit size
  const storyList = Array.isArray(stories)
    ? stories.slice(0, 20).map(s => typeof s === 'string' ? s.slice(0, 200) : '')
    : [];

  const apiKey = process.env.RESEND_API_KEY;

  try {
    const audienceId = await getOrCreateAudienceId(apiKey);

    // Add contact
    const contactResponse = await fetch(`https://api.resend.com/audiences/${audienceId}/contacts`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: normalizedEmail,
        unsubscribed: false,
        first_name: lang === 'cn' ? 'cn' : 'en',
        last_name: storyList.length > 0
          ? storyList.map(s => s.slice(0, 40)).join(' | ').slice(0, 200)
          : '',
      }),
    });

    if (!contactResponse.ok) {
      const contactError = await contactResponse.json().catch(() => ({}));
      // 409 means already exists - that's fine, continue to send welcome
      if (contactResponse.status !== 409) {
        console.error('Failed to add contact:', contactResponse.status, contactError);
        return res.status(500).json({ error: 'Server error' });
      }
    }

    // Send welcome email
    const storyCount = storyList.length;
    const emailResponse = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: process.env.RESEND_FROM_EMAIL || 'OldNews <onboarding@resend.dev>',
        to: normalizedEmail,
        subject: lang === 'cn'
          ? '👀 欢迎加入旧闻'
          : '👀 Welcome to OldNews',
        html: lang === 'cn'
          ? `<div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:40px 20px;">
              <h2 style="color:#2a3a40;">欢迎加入旧闻 👀</h2>
              <p style="color:#6a7a7e;line-height:1.6;">我们收到了你的邮箱。</p>
              <p style="color:#6a7a7e;line-height:1.6;">OldNews 还在准备中，上线后你会是第一批收到邮件的人。</p>
              ${storyCount > 0 ? `<p style="color:#6a7a7e;line-height:1.6;">你选了 ${storyCount} 条想盯的新闻，我们记下了。</p>` : ''}
              <p style="color:#b8956a;margin-top:24px;">— OldNews 旧闻</p>
            </div>`
          : `<div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:40px 20px;">
              <h2 style="color:#2a3a40;">Welcome to OldNews 👀</h2>
              <p style="color:#6a7a7e;line-height:1.6;">We've got your email.</p>
              <p style="color:#6a7a7e;line-height:1.6;">OldNews is still being built. You'll be among the first to know when we launch.</p>
              ${storyCount > 0 ? `<p style="color:#6a7a7e;line-height:1.6;">You picked ${storyCount} ${storyCount === 1 ? 'story' : 'stories'} to watch. We've noted them.</p>` : ''}
              <p style="color:#b8956a;margin-top:24px;">— OldNews</p>
            </div>`,
      }),
    });

    if (!emailResponse.ok) {
      console.error('Failed to send welcome email:', emailResponse.status);
      // Contact was added, don't fail the whole request
    }

    return res.status(200).json({ success: true });
  } catch (error) {
    console.error('Subscribe error:', error.message);
    return res.status(500).json({ error: 'Server error' });
  }
}
