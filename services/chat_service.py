# services/chat_service.py
import requests
import logging
import json
from config import OPENROUTER_API_KEY, YOUR_SITE_URL, YOUR_SITE_NAME
from urls import OPENROUTER_API_URL, OPENROUTER_MODEL_FREE, ERROR_NO_API_KEY, ERROR_NO_CONTENT, ERROR_TIMEOUT, ERROR_NON_JSON

def handle_chat_request(user_message: str):
    """
    Sends user message to OpenRouter and returns the generated reply.
    """

    if not OPENROUTER_API_KEY:
        logging.error(ERROR_NO_API_KEY)
        return ERROR_NO_API_KEY, 500

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    if YOUR_SITE_URL:
        headers["Referer"] = YOUR_SITE_URL
    if YOUR_SITE_NAME:
        headers["X-Title"] = YOUR_SITE_NAME

    payload = {
        "model": OPENROUTER_MODEL_FREE,
        "messages": [{"role": "user", "content": user_message}]
    }

    try:
        logging.info(f"Sending request to OpenRouter with model: {OPENROUTER_MODEL_FREE}")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=15)

        logging.info(f"OpenRouter returned status {response.status_code}")

        try:
            result = response.json()
        except json.JSONDecodeError:
            logging.error("Failed to decode OpenRouter response as JSON")
            return ERROR_NON_JSON, 502

        if response.status_code != 200:
            return result.get("error", {}).get("message", "API Error"), response.status_code

        reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not reply:
            logging.warning(f"No reply content found: {result}")
            return ERROR_NO_CONTENT, 500

        return reply, 200

    except requests.exceptions.Timeout:
        logging.error("OpenRouter request timed out.")
        return ERROR_TIMEOUT, 504
    except Exception as e:
        logging.error(f"Chat service error: {e}")
        return str(e), 500
