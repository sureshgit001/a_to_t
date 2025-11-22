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
from config import FLASK_PORT, DEBUG_MODE

app = Flask(__name__)
CORS(app)

# Setup logging
setup_logging()

# Register Blueprints
app.register_blueprint(ui_ai_routes)
app.register_blueprint(chat_routes)
app.register_blueprint(telegram_routes)
app.register_blueprint(affiliate_routes)
app.register_blueprint(amazon_bp, url_prefix="/amazon")
app.register_blueprint(send_amazon_product_to_telegram_bp)

# ---- Playwright INIT (SAFE FOR GUNICORN & RENDER) ----
@app.before_first_request
def initialize_playwright():
    try:
        logging.info("Starting Playwright browser...")
        BrowserManager.start(headless=True)
        logging.info("Playwright browser started successfully.")
    except Exception as e:
        logging.error(f"Failed to start Playwright: {e}")

# ---- SERVER START ----
if __name__ == "__main__":
    logging.info("Starting Flask app with Telegram Quote Scheduler...")
    # start_scheduler()

    port = int(os.environ.get("PORT", FLASK_PORT))
    app.run(host="0.0.0.0", port=port, debug=DEBUG_MODE, use_reloader=False, threaded=True)
