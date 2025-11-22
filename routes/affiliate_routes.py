from flask import Blueprint, request, jsonify
import logging
from services.affiliate_service import convert_to_affiliate

affiliate_routes = Blueprint("affiliate_routes", __name__)

@affiliate_routes.route("/convert", methods=["POST"])
def convert():
    """
    Convert Amazon URL into an affiliate link.
    Example Request JSON:
    {
        "url": "https://www.amazon.in/dp/B0CXYZ123/",
        "affiliate_id": "yourtag-21"
    }
    """
    try:
        data = request.get_json(force=True)
        url = data.get("url")
        affiliate_id = data.get("affiliate_id")

        if not url:
            return jsonify({"error": "Missing 'url' field"}), 400
        if not affiliate_id:
            return jsonify({"error": "Missing 'affiliate_id' field"}), 400

        affiliate_link = convert_to_affiliate(url, affiliate_id)
        return jsonify({
            "status": "success",
            "original_url": url,
            "affiliate_id": affiliate_id,
            "affiliate_link": affiliate_link
        }), 200

    except Exception as e:
        logging.error(f"Error in /convert: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
