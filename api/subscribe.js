export default async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { email, stories, lang } = req.body;

  if (!email || !email.includes('@')) {
    return res.status(400).json({ error: 'Invalid email' });
  }

  try {
    // Add contact to Resend audience
    const audienceResponse = await fetch('https://api.resend.com/audiences', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
      },
    });
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
      const newAudience = await createAudience.json();
      audienceId = newAudience.id;
    }

    // Add contact
    await fetch(`https://api.resend.com/audiences/${audienceId}/contacts`, {
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

    // Send welcome email
    await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: 'OldNews <hello@oldnews.io>',
        to: email,
        subject: lang === 'cn'
          ? '👀 欢迎加入旧闻'
          : '👀 Welcome to OldNews',
        html: lang === 'cn'
          ? `<div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:40px 20px;">
              <h2 style="color:#2a3a40;">欢迎加入旧闻 👀</h2>
              <p style="color:#6a7a7e;line-height:1.6;">我们收到了你的邮箱。</p>
              <p style="color:#6a7a7e;line-height:1.6;">OldNews 还在准备中，上线后你会是第一批收到邮件的人。</p>
              ${stories && stories.length > 0 ? `<p style="color:#6a7a7e;line-height:1.6;">你选了 ${stories.length} 条想盯的新闻，我们记下了。</p>` : ''}
              <p style="color:#b8956a;margin-top:24px;">— OldNews 旧闻</p>
            </div>`
          : `<div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:40px 20px;">
              <h2 style="color:#2a3a40;">Welcome to OldNews 👀</h2>
              <p style="color:#6a7a7e;line-height:1.6;">We've got your email.</p>
              <p style="color:#6a7a7e;line-height:1.6;">OldNews is still being built. You'll be among the first to know when we launch.</p>
              ${stories && stories.length > 0 ? `<p style="color:#6a7a7e;line-height:1.6;">You picked ${stories.length} stories to watch. We've noted them.</p>` : ''}
              <p style="color:#b8956a;margin-top:24px;">— OldNews</p>
            </div>`,
      }),
    });

    return res.status(200).json({ success: true });
  } catch (error) {
    console.error('Resend error:', error);
    return res.status(500).json({ error: 'Server error' });
  }
}
