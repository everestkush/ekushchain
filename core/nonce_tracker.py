import json
import os
import time

NONCE_FILE = '/tmp/everestkush_nonces.json'

class NonceTracker:
    @staticmethod
    def is_used(private_key, nonce):
        """Check if a nonce has been used for this private key"""
        try:
            with open(NONCE_FILE, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        
        key = f"{private_key}:{nonce}"
        return key in data
    
    @staticmethod
    def mark_used(private_key, nonce):
        """Mark a nonce as used"""
        try:
            with open(NONCE_FILE, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        
        key = f"{private_key}:{nonce}"
        data[key] = int(time.time())
        
        # Clean up old entries (older than 1 hour)
        now = int(time.time())
        data = {k: v for k, v in data.items() if now - v < 3600}
        
        with open(NONCE_FILE, 'w') as f:
            json.dump(data, f)
        
        return True
