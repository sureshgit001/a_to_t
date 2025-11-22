import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_amazon_product_to_telegram(product_data: dict, ai_summary: str = None):
    """
    Send Amazon product data to a Telegram chat.
    Includes AI summary first and orgUrl second.
    """
    try:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            raise Exception("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment variables")

        orgUrl = product_data.get("orgUrl", product_data.get("url", ""))

        # Prepare caption: AI summary first, then link
        caption_lines = []
        if ai_summary:
            caption_lines.append(f"{ai_summary}")  # AI summary first
        caption_lines.append(f"<b>{orgUrl}</b>")  # Link second (bold)
        caption = "\n\n".join(caption_lines)

        telegram_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

        # Send message to Telegram
        response = requests.post(
            f"{telegram_api}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": caption,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            },
            timeout=20
        )

        response.raise_for_status()
        logging.info("✅ Amazon product successfully sent to Telegram.")
        return {"success": True, "telegram_response": response.json()}

    except Exception as e:
        logging.error(f"❌ Error sending product to Telegram: {e}")
        return {"success": False, "error": str(e)}
