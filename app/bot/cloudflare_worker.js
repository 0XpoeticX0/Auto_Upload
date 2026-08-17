/**
 * Daily Dos of Islam - 24/7 Cloudflare Serverless Messenger AI Bot
 * 
 * Free 24/7 Hosting on Cloudflare Workers (No PC or server needed).
 * 
 * Environment Variables required in Cloudflare Worker Settings:
 * - FB_VERIFY_TOKEN: (e.g. daily_dos_islam_bot_verify_token)
 * - FB_ACCESS_TOKEN: Your Page Access Token
 * - GEMINI_API_KEY: Your Gemini API Key
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // 1. Webhook Verification (GET request from Meta)
    if (request.method === "GET") {
      const mode = url.searchParams.get("hub.mode");
      const token = url.searchParams.get("hub.verify_token");
      const challenge = url.searchParams.get("hub.challenge");

      const verifyToken = env.FB_VERIFY_TOKEN || "daily_dos_islam_bot_verify_token";

      if (mode === "subscribe" && token === verifyToken) {
        return new Response(challenge, { status: 200 });
      }
      return new Response("Forbidden", { status: 403 });
    }

    // 2. Incoming Messenger Messages (POST request from Meta)
    if (request.method === "POST") {
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
                  // Process in background
                  const ctx = { env, senderId, userText };
                  await handleMessengerReply(ctx);
                }
              }
            }
          }
          return new Response("EVENT_RECEIVED", { status: 200 });
        }
      } catch (err) {
        return new Response("Bad Request", { status: 400 });
      }
    }

    return new Response("Not Found", { status: 404 });
  }
};

async function handleMessengerReply({ env, senderId, userText }) {
  // 1. Send typing indicator
  await sendTyping(env.FB_ACCESS_TOKEN, senderId, "typing_on");

  // 2. Ask Gemini API for Islamic answer
  const aiReply = await askGemini(env.GEMINI_API_KEY, userText);

  // 3. Send message back to Facebook user
  await sendFbMessage(env.FB_ACCESS_TOKEN, senderId, aiReply);
  await sendTyping(env.FB_ACCESS_TOKEN, senderId, "typing_off");
}

async function askGemini(apiKey, text) {
  try {
    const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;
    const payload = {
      contents: [
        {
          role: "user",
          parts: [{ text: `${SYSTEM_PROMPT}\n\nUser Message: "${text}"\n\nReply in Bangla:` }]
        }
      ],
      generationConfig: {
        maxOutputTokens: 300,
        temperature: 0.7
      }
    };

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    return data.candidates?.[0]?.content?.parts?.[0]?.text || "আসসালামু আলাইকুম। Daily Dos of Islam-এ আপনাকে স্বাগতম। আমরা শীঘ্রই আপনার মেসেজের উত্তর দিব, ইনশাআল্লাহ।";
  } catch (e) {
    return "আসসালামু আলাইকুম। Daily Dos of Islam-এ আপনাকে স্বাগতম। জাযাকাল্লাহু খাইরান!";
  }
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
