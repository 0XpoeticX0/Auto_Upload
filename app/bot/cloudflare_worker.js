/**
 * Daily Dos of Islam - 24/7 Cloudflare Serverless Messenger AI Bot
 * 
 * Environment Variables required in Cloudflare Worker Settings:
 * - FB_VERIFY_TOKEN: daily_dos_islam_bot_verify_token
 * - FB_ACCESS_TOKEN: Your Page Access Token
 * - GEMINI_API_KEY: Your Gemini API Key (or GEMINI_API_KEYS with comma separation)
 * - CHAT_HISTORY: KV Namespace binding for maintaining 50-message conversation context
 */

const SYSTEM_PROMPT = `তুমি ফেসবুক পেজ 'Daily Dos of Islam'-এর একজন আন্তরিক, স্নেহশীল এবং প্রকৃত মানুষ প্রতিনিধি (দ্বীনি ভাই/বোন)।

কঠোর বানান ও ভাষার বিশুদ্ধতার নিয়ম (১০০% মেনে চলতে হবে):
১. বানানের বিশুদ্ধতা ও প্রমিত বাংলা:
   - জটিল বা যুক্তবর্ণের ভুল পরিহার করতে হবে। 'জিহ্বা/জিব্বা' লেখার বদলে সহজ, মার্জিত ও সুন্দর শব্দ যেমন 'জবান', 'মুখ' বা 'কথা' ব্যবহার করবে (যেমন: 'আমাদের জবান ও কথা সংযত রাখা উচিত')।
   - পরকালের জন্য শুদ্ধ বানান সর্বদা 'আখিরাত' বা 'আখেরাত' লিখবে। ভুল করেও 'আখেরোট' বা এমন বিকৃত বানান লিখবে না।
   - সঠিক ইসলামিক প্রমিত শব্দ: 'আল্লাহ', 'রাসূলুল্লাহ (ﷺ)', 'হাদিস', 'সালাত', 'তাওবাহ', 'আমল', 'কুরআন', 'জাযাকাল্লাহু খাইরান'।

২. প্রম্পট বা ইংরেজি লিক সম্পূর্ণ নিষেধ:
   - কোনো অবস্থাতেই ইংরেজি শব্দ (যেমন: 'Anchor', 'Pure, natural') বা কোনো লেবেল আউটপুটে লেখা যাবে না। শতভাগ শুদ্ধ বাংলা ভাষায় কথা বলবে।

৩. সর্বদা প্রসঙ্গ অনুযায়ী উত্তর দাও (অন্ধ উত্তর নিষেধ):
   - সাম্প্রতিক কথোপকথনের ইতিহাস ভালো করে পড়ে সেই অনুযায়ী উত্তর দাও।
   - কেউ ইমোজি (👍, ❤️, 😃) পাঠালে আগের প্রসঙ্গের সাথে মিলিয়ে আন্তরিক উত্তর দাও।
   - আগের কোনো প্রসঙ্গ না থাকলে (প্রথম মেসেজ বা হঠাৎ ইমোজি/ছবি আসলে), সুন্দরভাবে সালাম দিয়ে মিষ্টি ভাষায় জানতে চাও কীভাবে তাকে সাহায্য করতে পারো।

৪. হারাম বিষয়ে আপস নয় (১০০% হালাল ও শরিয়াহসম্মত):
   - কোনো হারাম সম্পর্ক (প্রেম/ডেটিং), সুদ, গান-বাজনা, মিথ্যা বা গুনাহকে কখনোই সমর্থন বা স্বাভাবিক করবে না। কেউ কষ্টে থাকলে বা পাপের কথা বললে মায়া ও দরদ দিয়ে তওবা ও আল্লাহর অফুরন্ত ক্ষমার দিকে ডাকো।

৫. মানুষের মতো সংক্ষিপ্ত ও হৃদয়স্পর্শী ভাষা:
   - খুব সংক্ষিপ্ত (১ থেকে ২টি ছোট বাক্যে, ২০ থেকে ৩৫ শব্দের মধ্যে) মানুষের মতো আন্তরিক ভাষায় কথা বলবে। কোনো কৃত্রিম বা রোবোটিক বাক্য বলা যাবে না।

৬. ছবি ও স্ক্রিনশট বিশ্লেষণ:
   - কেউ ছবি বা স্ক্রিনশট পাঠালে তা দেখে চলতি প্রসঙ্গের আলোকে অথবা সুন্দর ইসলামিক উপদেশ দিয়ে মিষ্টি ভাষায় উত্তর দাও।`;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 1. Webhook Verification (GET request from Meta)
    if (request.method === "GET") {
      const mode = url.searchParams.get("hub.mode");
      const token = url.searchParams.get("hub.verify_token");
      const challenge = url.searchParams.get("hub.challenge");

      const verifyToken = (env.FB_VERIFY_TOKEN || "daily_dos_islam_bot_verify_token").trim();

      if (mode === "subscribe" && token === verifyToken) {
        return new Response(challenge, { status: 200 });
      }
      return new Response("Daily Dos of Islam Bot Active", { status: 200 });
    }

    // 2. Incoming Messenger Messages (POST request from Meta)
    if (request.method === "POST") {
      try {
        const body = await request.json();

        if (body.object === "page") {
          const promises = [];

          for (const entry of body.entry || []) {
            const events = entry.messaging || entry.standby || [];
            for (const event of events) {
              const senderId = event.sender?.id;
              const message = event.message;

              // Ignore echoes
              if (message && !message.is_echo && senderId) {
                let userText = message.quick_reply?.payload || message.text || "";
                let imageUrl = null;

                // Check for image attachments
                if (message.attachments && Array.isArray(message.attachments)) {
                  for (const att of message.attachments) {
                    if (att.type === "image" && att.payload?.url) {
                      imageUrl = att.payload.url;
                      break;
                    }
                  }
                }

                // If user sent a thumbs up sticker or like without text
                if (!userText && message.sticker_id) {
                  userText = "👍";
                }

                if (userText || imageUrl) {
                  promises.push(handleMessengerReply({ env, senderId, userText, imageUrl }));
                }
              }
            }
          }

          if (promises.length > 0) {
            await Promise.all(promises);
          }

          return new Response("EVENT_RECEIVED", { status: 200 });
        }
      } catch (err) {
        console.error("[BOT] Webhook Error:", err);
        return new Response("EVENT_RECEIVED", { status: 200 });
      }
    }

    return new Response("Not Found", { status: 404 });
  }
};

function getGeminiKeys(env) {
  const keys = [];
  if (env.GEMINI_API_KEYS) {
    for (const k of env.GEMINI_API_KEYS.split(",")) {
      const clean = k.trim();
      if (clean && !keys.includes(clean)) keys.push(clean);
    }
  }
  const singleKeys = [
    env.GEMINI_KEY_5,
    env.GEMINI_API_KEY,
    env.GEMINI_KEY_3,
    env.GEMINI_KEY_4,
    env.GEMINI_BACKUP_API_KEY
  ];
  for (const k of singleKeys) {
    if (k) {
      const clean = k.trim();
      if (clean && !keys.includes(clean)) keys.push(clean);
    }
  }
  return keys;
}

let cachedPageToken = null;

async function getPageAccessToken(baseToken, targetPageId = "103994582489858") {
  if (cachedPageToken) return cachedPageToken;
  const clean = (baseToken || "").trim();
  if (!clean) return "";

  try {
    const meRes = await fetch(`https://graph.facebook.com/v20.0/me?fields=id&access_token=${clean}`);
    if (meRes.ok) {
      const meData = await meRes.json();
      if (meData.id === targetPageId) {
        cachedPageToken = clean;
        return clean;
      }
    }

    const res = await fetch(`https://graph.facebook.com/v20.0/me/accounts?access_token=${clean}`);
    if (res.ok) {
      const data = await res.json();
      for (const p of data.data || []) {
        if (p.id === targetPageId && p.access_token) {
          cachedPageToken = p.access_token;
          return p.access_token;
        }
      }
      if (data.data && data.data[0]?.access_token) {
        cachedPageToken = data.data[0].access_token;
        return data.data[0].access_token;
      }
    }
  } catch (e) {
    console.warn("[BOT] Token exchange notice:", e.message);
  }
  return clean;
}

function buildGeminiContents(history, currentText, imageBase64, imageMime) {
  const contents = [];
  let lastRole = null;
  for (const item of (history || [])) {
    if (!item.text || !item.role) continue;
    const role = item.role === "model" ? "model" : "user";
    if (role === lastRole) continue;
    contents.push({ role, parts: [{ text: item.text }] });
    lastRole = role;
  }
  if (contents.length > 0 && contents[0].role === "model") {
    contents.shift();
  }
  if (contents.length > 0 && contents[contents.length - 1].role === "user") {
    contents.pop();
  }

  const currentParts = [];
  if (currentText && currentText.trim()) {
    currentParts.push({ text: currentText });
  } else if (imageBase64) {
    currentParts.push({ text: "এই ছবিটি দেখে চলতি প্রসঙ্গের আলোকে সংক্ষেপে সুন্দর উপদেশ বা উত্তর দিন।" });
  } else {
    currentParts.push({ text: "👍" });
  }

  if (imageBase64) {
    currentParts.push({
      inline_data: {
        mime_type: imageMime || "image/jpeg",
        data: imageBase64
      }
    });
  }

  contents.push({ role: "user", parts: currentParts });
  return contents;
}

async function handleMessengerReply({ env, senderId, userText, imageUrl }) {
  const rawToken = env.FB_ACCESS_TOKEN || "";
  const fbToken = await getPageAccessToken(rawToken, env.FB_PAGE_ID || "103994582489858");
  const geminiKeys = getGeminiKeys(env);

  if (!fbToken || geminiKeys.length === 0) {
    console.error("[BOT] Missing FB_ACCESS_TOKEN or GEMINI_API_KEY in Worker Settings!");
    return;
  }

  try {
    console.log(`[BOT] Received message from ${senderId}: "${userText}" ${imageUrl ? '[Image Attached]' : ''}`);
    await sendTyping(fbToken, senderId, "typing_on");

    // 1. Fetch image if attached
    let imageBase64 = null;
    let imageMime = "image/jpeg";
    if (imageUrl) {
      try {
        const imgRes = await fetch(imageUrl);
        if (imgRes.ok) {
          const buffer = await imgRes.arrayBuffer();
          imageBase64 = btoa(String.fromCharCode(...new Uint8Array(buffer)));
          const ct = imgRes.headers.get("content-type");
          if (ct) imageMime = ct;
        }
      } catch (imgErr) {
        console.warn("[BOT] Could not download attachment image:", imgErr.message);
      }
    }

    // 2. Retrieve the last 50 messages from KV
    let history = [];
    const threadKey = `thread_${senderId}`;
    if (env.CHAT_HISTORY) {
      try {
        const stored = await env.CHAT_HISTORY.get(threadKey, "json");
        if (Array.isArray(stored)) {
          history = stored.slice(-50);
        }
      } catch (kvReadErr) {
        console.warn("[BOT] Could not read thread history from KV:", kvReadErr.message);
      }
    }

    // 3. Ask Gemini with full 50-message context, Vision, and low temperature (0.3) for perfect spelling
    const aiReply = await askGemini(geminiKeys, userText, history, imageBase64, imageMime);
    console.log(`[BOT] Generated AI Reply: "${aiReply.substring(0, 60)}..."`);

    // 4. Deliver message back to Messenger
    await sendFbMessage(fbToken, senderId, aiReply);
    await sendTyping(fbToken, senderId, "typing_off");

    // 5. Update thread in KV (last 50 messages)
    if (env.CHAT_HISTORY) {
      try {
        const savedUserMsg = userText || (imageUrl ? "[ছবি পাঠানো হয়েছে]" : "👍");
        history.push({ role: "user", text: savedUserMsg });
        history.push({ role: "model", text: aiReply });
        const updatedHistory = history.slice(-50);
        await env.CHAT_HISTORY.put(threadKey, JSON.stringify(updatedHistory), {
          expirationTtl: 60 * 60 * 24 * 30
        });
      } catch (kvWriteErr) {
        console.warn("[BOT] Failed to write thread to CHAT_HISTORY KV:", kvWriteErr.message);
      }
    }
  } catch (err) {
    console.error("[BOT] Error in handleMessengerReply:", err);
  }
}

const MODELS_BEST_TO_WORST = [
  "gemini-3.5-flash-lite",
  "gemini-3.8-flash",
  "gemini-3.5-flash",
  "gemini-flash-latest"
];

async function askGemini(keys, text, history = [], imageBase64 = null, imageMime = "image/jpeg") {
  if (!keys || keys.length === 0) {
    console.error("[GEMINI] No API keys configured in Worker!");
    return "আসসালামু আলাইকুম। Daily Dos of Islam-এ আপনাকে স্বাগতম। আমরা শীঘ্রই আপনার মেসেজের উত্তর দিব, ইনশাআল্লাহ। জাযাকাল্লাহু খাইরান!";
  }

  const contents = buildGeminiContents(history, text, imageBase64, imageMime);

  for (const model of MODELS_BEST_TO_WORST) {
    for (const key of keys) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 7000);

        const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`;
        const payload = {
          system_instruction: {
            parts: [{ text: SYSTEM_PROMPT }]
          },
          contents: contents,
          generationConfig: {
            maxOutputTokens: 120,
            temperature: 0.3 // Strict low temperature eliminates spelling scramble and hallucinations
          }
        };

        const res = await fetch(endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-goog-api-key": key
          },
          body: JSON.stringify(payload),
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (res.ok) {
          const data = await res.json();
          const reply = data.candidates?.[0]?.content?.parts?.[0]?.text;
          if (reply && reply.trim()) {
            console.log(`[GEMINI] Fast response delivered with ${model}`);
            return reply.trim();
          }
        }
      } catch (e) {
        console.warn(`[GEMINI] Error with ${model}:`, e.message);
      }
    }
  }

  return "আসসালামু আলাইকুম। Daily Dos of Islam-এ আপনাকে স্বাগতম। আমরা শীঘ্রই আপনার মেসেজের উত্তর দিব, ইনশাআল্লাহ। জাযাকাল্লাহু খাইরান!";
}

async function sendFbMessage(accessToken, recipientId, text) {
  const cleanToken = accessToken.trim();
  const url = `https://graph.facebook.com/v20.0/me/messages?access_token=${cleanToken}`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recipient: { id: recipientId },
        message: { text: text },
        messaging_type: "RESPONSE"
      })
    });
    const data = await res.json();
    if (res.ok && data.message_id) {
      console.log(`[FB_SEND] Delivered to ${recipientId}: ${data.message_id}`);
    }
  } catch (err) {
    console.error("[FB_SEND] Failed to fetch Graph API:", err);
  }
}

async function sendTyping(accessToken, recipientId, action) {
  const cleanToken = accessToken.trim();
  const url = `https://graph.facebook.com/v20.0/me/messages?access_token=${cleanToken}`;
  try {
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recipient: { id: recipientId },
        sender_action: action
      })
    });
  } catch (err) {}
}
