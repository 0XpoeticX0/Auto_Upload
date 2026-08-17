import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from app.logger import logger
from app.bot.handler import generate_ai_bot_reply
from app.bot.messenger import send_messenger_reply, send_typing_indicator

VERIFY_TOKEN = os.environ.get("FB_VERIFY_TOKEN", "daily_dos_islam_bot_verify_token")

class MessengerWebhookHandler(BaseHTTPRequestHandler):
    def _send_response_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        """Handle Meta Webhook Verification Challenge."""
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/webhook" or parsed_url.path == "/":
            query_params = parse_qs(parsed_url.query)
            mode = query_params.get("hub.mode", [""])[0]
            token = query_params.get("hub.verify_token", [""])[0]
            challenge = query_params.get("hub.challenge", [""])[0]

            if mode == "subscribe" and token == VERIFY_TOKEN:
                logger.info("Meta Webhook successfully verified!")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(challenge.encode("utf-8"))
            else:
                logger.warning(f"Webhook verification failed. Token received: {token}")
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle incoming Messenger message events from Meta."""
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/webhook" or parsed_url.path == "/":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception as e:
                logger.error(f"Failed to parse webhook JSON: {e}")
                self._send_response_json(400, {"error": "Invalid JSON"})
                return

            # Acknowledge Meta immediately with 200 OK so it doesn't retry
            self._send_response_json(200, {"status": "EVENT_RECEIVED"})

            if data.get("object") == "page":
                for entry in data.get("entry", []):
                    for messaging_event in entry.get("messaging", []):
                        sender_id = messaging_event.get("sender", {}).get("id")
                        message = messaging_event.get("message", {})

                        # Ignore echoes or delivery receipts
                        if message.get("is_echo") or not sender_id:
                            continue

                        user_text = message.get("text", "")
                        quick_reply = message.get("quick_reply", {}).get("payload")
                        final_text = quick_reply or user_text

                        if final_text:
                            # Process AI reply asynchronously so we don't block
                            threading.Thread(target=self._process_and_reply, args=(sender_id, final_text)).start()
        else:
            self.send_response(404)
            self.end_headers()

    def _process_and_reply(self, sender_id: str, text: str):
        logger.info(f"Incoming message from PSID {sender_id}: '{text}'")
        
        # 1. Send typing indicator
        send_typing_indicator(sender_id, "mark_seen")
        send_typing_indicator(sender_id, "typing_on")

        # 2. Generate Islamic AI answer
        ai_reply = generate_ai_bot_reply(text)

        # 3. Send reply back to user
        send_messenger_reply(sender_id, ai_reply)
        send_typing_indicator(sender_id, "typing_off")

def run_server(port: int = 8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, MessengerWebhookHandler)
    logger.info(f"Islamic Messenger AI Bot Webhook running on port {port}...")
    logger.info(f"Webhook URL for Meta App: http://your-domain-or-ngrok.com/webhook")
    logger.info(f"Verify Token: {VERIFY_TOKEN}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping bot server...")
        httpd.server_close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port)
