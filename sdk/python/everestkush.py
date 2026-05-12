"""
EverestKush Python SDK
Client-side wallet and transaction signing
"""
import hashlib
import json
import requests
import socketio
from typing import Dict, Any, Optional
from dataclasses import dataclass
import secrets

@dataclass
class Wallet:
    address: str
    public_key: str
    private_key: str  # NEVER send to server

class EverestKushClient:
    def __init__(self, api_url: str = "http://103.74.15.88:5000"):
        self.api_url = api_url
        self.session = requests.Session()
    
    @staticmethod
    def generate_wallet() -> Wallet:
        """Generate new wallet (client-side only)"""
        # Generate secure random private key
        private_key = secrets.token_hex(32)
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        address = f"ekush{public_key[:40]}"
        
        return Wallet(
            address=address,
            public_key=public_key,
            private_key=private_key
        )
    
    def sign_transaction(self, tx: Dict, private_key: str) -> Dict:
        """Sign transaction client-side"""
        tx_hash = hashlib.sha256(json.dumps(tx).encode()).hexdigest()
        signature = hashlib.sha256(f"{tx_hash}{private_key}".encode()).hexdigest()
        
        return {
            **tx,
            'signature': signature,
            'public_key': hashlib.sha256(private_key.encode()).hexdigest()
        }
    
    def broadcast_transaction(self, signed_tx: Dict) -> Dict:
        """Broadcast signed transaction to network"""
        response = self.session.post(
            f"{self.api_url}/transaction/broadcast",
            json=signed_tx
        )
        return response.json()
    
    def get_balance(self, address: str) -> Dict:
        """Get address balance"""
        response = self.session.get(f"{self.api_url}/balance/{address}")
        return response.json()
    
    def get_stats(self) -> Dict:
        """Get blockchain stats"""
        response = self.session.get(f"{self.api_url}/api/stats")
        return response.json()
    
    def subscribe_websocket(self, address: str, callback):
        """Subscribe to real-time balance updates"""
        sio = socketio.Client()
        
        @sio.event
        def connect():
            sio.emit('subscribe_balance', {'address': address})
        
        @sio.on('balance_update')
        def on_balance(data):
            callback(data)
        
        sio.connect('http://localhost:5001')
        return sio

# Example usage
if __name__ == "__main__":
    # Generate wallet
    wallet = EverestKushClient.generate_wallet()
    print(f"Address: {wallet.address}")
    print(f"Private Key: {wallet.private_key}")
    print("⚠️ NEVER share private key!")
    
    # Check balance
    client = EverestKushClient()
    balance = client.get_balance(wallet.address)
    print(f"Balance: {balance}")
