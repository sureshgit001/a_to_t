import requests
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message: str):
    """
    Sends a message to Telegram using the bot token and chat ID.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("Telegram bot token or chat ID is missing.")
        return {"error": "Telegram configuration missing"}, 500

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            return {"status": "success", "message": "Message sent to Telegram"}, 200
        else:
            logging.error(f"Telegram API error: {response.text}")
            return {"error": response.text}, response.status_code
    except Exception as e:
        logging.error(f"Telegram request error: {e}")
        return {"error": str(e)}, 500
