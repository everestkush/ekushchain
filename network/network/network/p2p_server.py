
# Add message handling for sync
from .p2p_handler import handle_message

def _handle_client_data(self, client, data):
    try:
        msg = json.loads(data.decode())
        msg_type = msg.get('type')
        payload = msg.get('payload', {})
        
        response = handle_message(self, msg_type, payload)
        if response:
            client.send(json.dumps(response).encode())
    except Exception as e:
        print(f"Error handling message: {e}")
