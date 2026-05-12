import time
import json

class VersionNegotiation:
    PROTOCOL_VERSION = 70015
    USER_AGENT = "/EverestKush:2.0/"
    
    def __init__(self, local_height=0):
        self.local_height = local_height
    
    def create_version_message(self):
        return json.dumps({
            "version": self.PROTOCOL_VERSION,
            "services": 1,
            "timestamp": int(time.time()),
            "user_agent": self.USER_AGENT,
            "start_height": self.local_height,
            "relay": True
        }).encode()
    
    def parse_version(self, data):
        try:
            msg = json.loads(data.decode())
            return {
                "version": msg.get("version", 0),
                "user_agent": msg.get("user_agent", ""),
                "start_height": msg.get("start_height", 0)
            }
        except:
            return None
    
    def negotiate(self, peer_version):
        if peer_version["version"] < 70000:
            return {"accept": False, "reason": "Protocol version too old"}
        return {"accept": True, "version": self.PROTOCOL_VERSION}
