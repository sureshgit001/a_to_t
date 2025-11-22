from flask import Blueprint, request, jsonify
import logging
from services.amazon_service import expand_amazon_url, scrape_amazon_details
from services.send_amazon_product_to_telegram_service import send_amazon_product_to_telegram
from services.chat_service import handle_chat_request

send_amazon_product_to_telegram_bp = Blueprint("send_amazon_product_to_telegram_bp", __name__)

@send_amazon_product_to_telegram_bp.route("/telegram/send-amazon-product", methods=["GET"])
def send_amazon_product_to_telegram_route():
    """
    Fetch product info from Amazon using the existing amazon_service,
    generate an AI summary via OpenRouter, and send that data to Telegram.
    Example:
        /telegram/send-amazon-product?url=https://amzn.to/4q2qwct
    """
    org_url = request.args.get("url")
    if not org_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        # Step 1: Expand short URL if needed
        full_url = expand_amazon_url(org_url)

        # Step 2: Scrape product details using amazon_service
        product_data = scrape_amazon_details(full_url, org_url)
        if "error" in product_data:
            return jsonify({"error": "Failed to fetch product details", "details": product_data}), 500

        # --- Step 2.5: Generate AI message using OpenRouter ---
        user_message = (
            f"Product Details:\n"
            f"Title: {product_data.get('title', 'N/A')}\n"
            f"Price: {product_data.get('price', 'N/A')}\n"
            f"discount: {product_data.get('discount', 'N/A')}\n"
           # f"Discount: {product_data.get('discount', 'N/A')}\n"
           # f"Link: {product_data.get('orgURl', 'N/A')}\n\n"
            "Provide a short ,concise and engaging meassage for Telegram"

        )

        ai_reply, status = handle_chat_request(user_message)
        if status != 200:
            logging.warning(f"AI chat service failed: {ai_reply}")
            ai_reply = None  # fallback in case AI fails

        # Step 3: Send scraped data to Telegram (including AI summary if available)
        telegram_response = send_amazon_product_to_telegram(product_data, ai_reply)

        return jsonify({
            
            "product_title": product_data,
            "ai_summary": ai_reply,
           
        })

        #    # Step 3: Send scraped data to Telegram (including AI summary if available)
        # telegram_response = send_amazon_product_to_telegram(product_data, ai_reply)
        #  return jsonify({
        #     "status": "success" if telegram_response.get("success") else "failed",
        #     "product_title": product_data.get("title"),
        #     "ai_summary": ai_reply,
        #     "telegram_response": telegram_response
        # })

    except Exception as e:
        logging.error(f"❌ Error in /telegram/send-amazon-product: {e}")
        return jsonify({"error": str(e)}), 500
