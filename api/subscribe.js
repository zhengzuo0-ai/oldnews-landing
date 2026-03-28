export default async function handler(req, res) {
  // CORS - restrict to our domain (allow all in development)
  const allowedOrigins = ['https://oldnews.io', 'https://www.oldnews.io'];
  const origin = req.headers.origin;
  if (allowedOrigins.includes(origin)) {
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

  if (!process.env.RESEND_API_KEY) {
    console.error('RESEND_API_KEY is not configured');
    return res.status(500).json({ error: 'Server configuration error' });
  }

  const { email, stories, lang } = req.body;

  // Stronger email validation
  if (!email || typeof email !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ error: 'Invalid email' });
  }

  // Validate stories is an array if provided
  const storyList = Array.isArray(stories) ? stories : [];

  try {
    // Add contact to Resend audience
    const audienceResponse = await fetch('https://api.resend.com/audiences', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
      },
    });

    if (!audienceResponse.ok) {
      console.error('Failed to fetch audiences:', audienceResponse.status);
      return res.status(500).json({ error: 'Server error' });
    }

    const audiences = await audienceResponse.json();

    // Use first audience or create one
    let audienceId;
    if (audiences.data && audiences.data.length > 0) {
      audienceId = audiences.data[0].id;
    } else {
      const createAudience = await fetch('https://api.resend.com/audiences', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: 'OldNews Subscribers' }),
      });
      if (!createAudience.ok) {
        console.error('Failed to create audience:', createAudience.status);
        return res.status(500).json({ error: 'Server error' });
      }
      const newAudience = await createAudience.json();
      audienceId = newAudience.id;
    }

    // Add contact
    const contactResponse = await fetch(`https://api.resend.com/audiences/${audienceId}/contacts`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        unsubscribed: false,
        first_name: '',
        last_name: '',
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
        'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: process.env.RESEND_FROM_EMAIL || 'OldNews <onboarding@resend.dev>',
        to: email,
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
              ${storyCount > 0 ? `<p style="color:#6a7a7e;line-height:1.6;">You picked ${storyCount} stories to watch. We've noted them.</p>` : ''}
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
