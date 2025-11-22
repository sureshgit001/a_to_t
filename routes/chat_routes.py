from flask import Blueprint, request, jsonify
from services.chat_service import handle_chat_request
import logging
from urls import ROUTE_CHAT, ERROR_INVALID_JSON, ERROR_NO_MESSAGE

chat_routes = Blueprint("chat_routes", __name__)

@chat_routes.route(ROUTE_CHAT, methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": ERROR_INVALID_JSON}), 400

        user_message = data.get("message", "")
        if not user_message:
            return jsonify({"error": ERROR_NO_MESSAGE}), 400

        reply, status_code = handle_chat_request(user_message)
        return jsonify({"reply": reply}), status_code

    except Exception as e:
        logging.error(f"Unexpected error in /chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500
