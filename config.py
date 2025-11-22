import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Flask settings
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

# OpenRouter settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
YOUR_SITE_URL = os.getenv("YOUR_SITE_URL", "")
YOUR_SITE_NAME = os.getenv("YOUR_SITE_NAME", "")

# Telegram settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

QUOTE_MESSAGE = os.getenv(
    "QUOTE_MESSAGE",
    "Give me an inspiring quote or romantic add emojis according to quote - dont mention author name, remove double quotes at starting and ending"
)

try:
    SCHEDULER_INTERVAL_MINUTES = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "1"))
except ValueError:
    SCHEDULER_INTERVAL_MINUTES = 1