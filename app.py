from flask import Flask
from routes.home_route import home_routes
from routes.chat_routes import chat_routes
from routes.telegram_routes import telegram_routes
from scheduler.telegram_quote_scheduler import start_scheduler
from routes.affiliate_routes import affiliate_routes
from routes.amazon_routes import amazon_bp
from utils.logger import setup_logging
from routes.send_amazon_product_to_telegram_routes import send_amazon_product_to_telegram_bp
from services.playwright_amazon_service import BrowserManager
from routes.ui_routes import ui_ai_routes

from flask_cors import CORS
import logging
import os

app = Flask(__name__)
CORS(app)

initialized = False  # one-time init flag

@app.before_request
def initialize_playwright():
    global initialized
    if not initialized:
        try:
            logging.info("Starting Playwright browser...")
            BrowserManager.start(headless=True)
            logging.info("Playwright started successfully.")
        except Exception as e:
            logging.error(f"Playwright startup failed: {e}")
        initialized = True

setup_logging()

app.register_blueprint(ui_ai_routes)
app.register_blueprint(chat_routes)
app.register_blueprint(telegram_routes)
app.register_blueprint(affiliate_routes)
app.register_blueprint(amazon_bp, url_prefix="/amazon")
app.register_blueprint(send_amazon_product_to_telegram_bp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)
