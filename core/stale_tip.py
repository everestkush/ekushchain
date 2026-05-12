import time
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class StaleTipDetector:
    def __init__(self, alert_minutes=30, webhook_url=None):
        self.alert_minutes = alert_minutes
        self.webhook_url = webhook_url
        self.last_alert_time = 0
    
    def check(self, current_height: int, last_block_time: int, peer_heights: list):
        now = int(time.time())
        age_minutes = (now - last_block_time) / 60
        
        if age_minutes > self.alert_minutes:
            median_peer = sorted(peer_heights)[len(peer_heights)//2] if peer_heights else 0
            alert = {
                "level": "WARNING" if age_minutes > 60 else "INFO",
                "message": f"Chain tip is {age_minutes:.0f} minutes old",
                "current_height": current_height,
                "peer_height": median_peer,
                "diff": median_peer - current_height,
                "timestamp": datetime.now().isoformat()
            }
            logger.warning(json.dumps(alert))
            return alert
        return None
