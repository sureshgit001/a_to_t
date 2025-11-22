from flask import Blueprint, request, jsonify
import logging
from services.chat_service import handle_chat_request
from services.telegram_service import send_telegram_message
from urls import ERROR_INVALID_JSON, ERROR_NO_MESSAGE

telegram_routes = Blueprint("telegram_routes", __name__)

@telegram_routes.route("/send-quote-from-chat", methods=["POST"])
def send_quote_from_chat():
    """
    Get quote from chat service and send it to Telegram.
    Request JSON:
    {
        "message": "Give me an inspiring quote"
    }
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": ERROR_INVALID_JSON}), 400

        user_message = data.get("message", "")
        if not user_message:
            return jsonify({"error": ERROR_NO_MESSAGE}), 400

        # Step 1 — Get reply from chat service
        reply, status_code = handle_chat_request(user_message)

        if status_code != 200:
            return jsonify({"error": reply}), status_code

        # Step 2 — Send reply to Telegram
        telegram_result, telegram_status = send_telegram_message(reply)

        return jsonify({
            "reply": reply,
            "telegram_status": telegram_status,
            "telegram_result": telegram_result
        }), 200

    except Exception as e:
        logging.error(f"Error in /send-quote-from-chat: {e}")
        return jsonify({"error": str(e)}), 500
