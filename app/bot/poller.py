import os
import time
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

from app.logger import logger
from app.bot.handler import generate_ai_bot_reply
from app.bot.messenger import get_page_access_token, send_messenger_reply, send_typing_indicator

# Load environment
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(ENV_PATH)

PAGE_ID = os.environ.get("FB_PAGE_ID", "103994582489858").strip()
REPLIED_LOG_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "bot_replied_ids.json"

def load_replied_ids() -> set:
    if not REPLIED_LOG_FILE.exists():
        return set()
    try:
        with open(REPLIED_LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data)
    except Exception as e:
        logger.warning(f"Could not load bot_replied_ids.json: {e}")
        return set()

def save_replied_id(msg_id: str):
    current = load_replied_ids()
    current.add(msg_id)
    REPLIED_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPLIED_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(list(current), f, indent=2)

def poll_inbox_and_reply(limit: int = 10) -> int:
    """
    Polls the Page inbox for new unread/incoming messages and generates
    Gemini AI auto-replies.
    Returns the count of replies sent.
    """
    page_token = get_page_access_token()
    if not page_token:
        logger.error("No valid Page Access Token available for polling.")
        return 0

    replied_ids = load_replied_ids()
    replies_count = 0

    url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/conversations"
    params = {
        "fields": "id,snippet,updated_time,unread_count,senders,messages.limit(2){id,message,created_time,from}",
        "limit": limit,
        "access_token": page_token
    }

    try:
        res = requests.get(url, params=params, timeout=15)
        res_data = res.json()
    except Exception as e:
        logger.error(f"Failed to fetch conversations from Facebook: {e}")
        return 0

    if "error" in res_data:
        logger.error(f"Graph API error when fetching conversations: {res_data['error']}")
        return 0

    conversations = res_data.get("data", [])
    logger.info(f"Checking {len(conversations)} conversation threads in Page inbox...")

    for conv in conversations:
        conv_id = conv.get("id")
        messages_data = conv.get("messages", {}).get("data", [])
        if not messages_data:
            continue

        latest_msg = messages_data[0]
        msg_id = latest_msg.get("id")
        msg_text = (latest_msg.get("message") or "").strip()
        sender_info = latest_msg.get("from", {})
        sender_id = str(sender_info.get("id", ""))
        sender_name = sender_info.get("name", "Unknown")

        # Skip if message is from the page itself
        if sender_id == str(PAGE_ID):
            continue

        # Skip if message has no text or already replied
        if not msg_text:
            continue

        if msg_id in replied_ids:
            continue

        logger.info(f"Incoming message from {sender_name} (ID: {sender_id}): '{msg_text}'")

        # 1. Send typing indicator
        send_typing_indicator(sender_id, "mark_seen")
        send_typing_indicator(sender_id, "typing_on")

        # 2. Generate authentic Islamic reply using Gemini
        try:
            ai_reply = generate_ai_bot_reply(msg_text)
            logger.info(f"Gemini AI response ready: '{ai_reply[:60]}...'")
        except Exception as e:
            logger.error(f"Gemini AI generation failed: {e}")
            send_typing_indicator(sender_id, "typing_off")
            continue

        # 3. Deliver reply via Send API
        success = send_messenger_reply(sender_id, ai_reply)
        send_typing_indicator(sender_id, "typing_off")

        if success:
            save_replied_id(msg_id)
            replies_count += 1
            logger.info(f"Replied to {sender_name} successfully.")
        else:
            logger.warning(f"Could not send reply to {sender_name} (PSID: {sender_id}).")

    return replies_count

def run_loop(interval_seconds: int = 25):
    logger.info(f"Starting Facebook Page Messenger Auto-Reply Poller (Interval: {interval_seconds}s)...")
    logger.info("Press Ctrl+C to stop.")
    while True:
        try:
            poll_inbox_and_reply()
        except KeyboardInterrupt:
            logger.info("Poller stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in poller loop: {e}")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Page Messenger Auto-Reply Poller")
    parser.add_argument("--loop", action="store_true", help="Run continuously in background polling mode")
    parser.add_argument("--interval", type=int, default=25, help="Polling interval in seconds (default: 25)")
    parser.add_argument("--once", action="store_true", help="Run a single polling cycle and exit")
    args = parser.parse_args()

    if args.loop:
        run_loop(args.interval)
    else:
        sent = poll_inbox_and_reply()
        print(f"Cycle completed. Replies sent: {sent}")
