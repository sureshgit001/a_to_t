from apscheduler.schedulers.background import BackgroundScheduler
import logging
import requests
import json
from config import QUOTE_MESSAGE, SCHEDULER_INTERVAL_MINUTES

def send_quote_to_telegram():
    """
    Calls /send-quote-from-chat endpoint automatically.
    """
    try:
        logging.info("Scheduler triggered: sending quote to Telegram.")

        url = "http://127.0.0.1:5000/send-quote-from-chat"
        headers = {"Content-Type": "application/json"}
        body = {"message": QUOTE_MESSAGE}

        response = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)

        if response.status_code == 200:
            logging.info(f"Quote sent successfully: {response.json()}")
        else:
            logging.error(f"Failed to send quote: {response.status_code} {response.text}")

    except Exception as e:
        logging.error(f"Error in scheduler task: {e}")


import os

def start_scheduler():
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":  # Only run in main process
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(send_quote_to_telegram, "interval", minutes=SCHEDULER_INTERVAL_MINUTES)
        scheduler.start()
        logging.info(f"Telegram quote scheduler started. Interval: {SCHEDULER_INTERVAL_MINUTES} minute(s).")
