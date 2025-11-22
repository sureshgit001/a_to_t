from flask import Blueprint, request, jsonify
import logging
#from services.amazon_service import expand_amazon_url, scrape_amazon_details
from services.playwright_amazon_service import expand_amazon_url, scrape_amazon_details


amazon_bp = Blueprint("amazon", __name__)

@amazon_bp.route("/amazon-info", methods=["GET"])
def amazon_info():
    """
    GET /amazon/amazon-info?url=<amazon_url>
    """
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Please provide a 'url' parameter"}), 400

    try:
        # Expand short URL if needed
        orgURL = url
        if "amzn.to" in url:
            shortUrl = expand_amazon_url(url)

        # Scrape product details
        product_data = scrape_amazon_details(shortUrl,orgURL)

        if "error" in product_data:
            return jsonify(product_data), 502

        return jsonify(product_data), 200

    except Exception as e:
        logging.exception("Unhandled exception in /amazon-info")
        return jsonify({"error": str(e)}), 500
