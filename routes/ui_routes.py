from flask import Blueprint, render_template

ui_ai_routes = Blueprint("ui_ai_routes", __name__)

@ui_ai_routes.route("/amazon-ai", methods=["GET"])
def amazon_ai_ui():
    """Render UI for Amazon to Telegram with AI"""
    return render_template("amazon_ai_form.html")
