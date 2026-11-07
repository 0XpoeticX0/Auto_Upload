/**
 * Cloudflare Pages Functions - Facebook Messenger Gemini AI Bot
 * Catches all routes (/, /webhook) on islamic-messenger-bot.pages.dev
 */

const SYSTEM_PROMPT = `You are 'Daily Dos of Islam Bot', an Islamic Dawah & Spiritual Support AI for the Facebook page 'Daily Dos of Islam'.

YOUR OBJECTIVES:
1. Greet politely in Bangla (আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ).
2. Answer Islamic questions, queries about mental peace/duas, daily life rulings, and hadith references with 100% authentic Quran & Sahih Hadith sources.
3. If someone asks about the page or advertisement ("Can you tell me more about your ad/business?"):
   - Explain warmly that Daily Dos of Islam is a dedicated Islamic Dawah platform sharing authentic Quran, Hadith, and emotional reminders.
   - Encourage them to follow the page and check our daily video shorts and photo cards.
4. If someone expresses sadness, anxiety, or asks for a Dua:
   - Comfort them with empathy and provide authentic Sahih Duas (with Arabic, Bangla pronunciation, and meaning).
5. TONE: Warm, gentle, deeply respectful, polite, and encouraging.
6. LENGTH: Keep responses concise and easy to read on a mobile chat screen (under 150 words). Avoid overwhelming walls of text.`;

export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);

  const mode = url.searchParams.get("hub.mode");
  const token = url.searchParams.get("hub.verify_token");
  const challenge = url.searchParams.get("hub.challenge");

  const verifyToken = env.FB_VERIFY_TOKEN || "daily_dos_islam_bot_verify_token";

  if (mode === "subscribe" && token === verifyToken) {
    return new Response(challenge, { status: 200 });
  }
  return new Response("Daily Dos of Islam Bot - Webhook Ready", { status: 200 });
}

export async function onRequestPost(context) {
  const { request, env } = context;

  try {
    const body = await request.json();

    if (body.object === "page") {
      for (const entry of body.entry || []) {
        for (const event of entry.messaging || []) {
          const senderId = event.sender?.id;
          const message = event.message;

          if (message && !message.is_echo && senderId) {
            const userText = message.quick_reply?.payload || message.text;
            if (userText) {
              context.waitUntil(handleMessengerReply({ env, senderId, userText }));
            }
          }
        }
      }
      return new Response("EVENT_RECEIVED", { status: 200 });
    }
  } catch (err) {
    return new Response("Bad Request", { status: 400 });
  }

  return new Response("OK", { status: 200 });
}

async function handleMessengerReply({ env, senderId, userText }) {
  await sendTyping(env.FB_ACCESS_TOKEN, senderId, "typing_on");
  const aiReply = await askGemini(env.GEMINI_API_KEY, userText);
  await sendFbMessage(env.FB_ACCESS_TOKEN, senderId, aiReply);
  await sendTyping(env.FB_ACCESS_TOKEN, senderId, "typing_off");
}

async function askGemini(apiKey, text) {
  const models = ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.1-flash-lite"];
  for (const model of models) {
    try {
      const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
      const payload = {
        contents: [
          {
            role: "user",
            parts: [{ text: `${SYSTEM_PROMPT}\n\nUser Message: "${text}"\n\nReply in Bangla:` }]
          }
        ],
        generationConfig: {
          maxOutputTokens: 250,
          temperature: 0.7
        }
      };

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        const reply = data.candidates?.[0]?.content?.parts?.[0]?.text;
        if (reply && reply.trim()) return reply.trim();
      }
    } catch (e) {
      // try next model
    }
  }
  return "আসসালামু আলাইকুম। Daily Dos of Islam-এ আপনাকে স্বাগতম। আমরা শীঘ্রই আপনার মেসেজের উত্তর দিব, ইনশাআল্লাহ। জাযাকাল্লাহু খাইরান!";
}

async function sendFbMessage(accessToken, recipientId, text) {
  const url = `https://graph.facebook.com/v20.0/me/messages?access_token=${accessToken}`;
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      recipient: { id: recipientId },
      message: { text: text },
      messaging_type: "RESPONSE"
    })
  });
}

async function sendTyping(accessToken, recipientId, action) {
  const url = `https://graph.facebook.com/v20.0/me/messages?access_token=${accessToken}`;
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      recipient: { id: recipientId },
      sender_action: action
    })
  });
}
