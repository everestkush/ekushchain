import requests
import json
import threading
import logging

logger = logging.getLogger(__name__)

class WebhookNotifier:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url
    
    def send(self, event_type, data):
        if not self.webhook_url:
            return
        threading.Thread(target=self._post, args=(event_type, data), daemon=True).start()
    
    def _post(self, event_type, data):
        try:
            payload = {"event": event_type, "data": data}
            requests.post(self.webhook_url, json=payload, timeout=2)
        except Exception as e:
            logger.debug(f"Webhook failed: {e}")
