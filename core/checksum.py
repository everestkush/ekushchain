import json
"""
Message Checksum Validation - Bitcoin Standard
Ensures P2P message integrity with 4-byte checksums
"""

import hashlib
import struct

def calculate_checksum(data):
    """
    Calculate 4-byte checksum from data (Bitcoin standard)
    First 4 bytes of double SHA256
    """
    if isinstance(data, str):
        data = data.encode()
    hash1 = hashlib.sha256(data).digest()
    hash2 = hashlib.sha256(hash1).digest()
    return hash2[:4]  # First 4 bytes

def verify_checksum(data, checksum):
    """Verify that checksum matches data"""
    expected = calculate_checksum(data)
    return expected == checksum

def add_checksum(message):
    """Add checksum to a message"""
    # Message format: [checksum(4)][payload]
    payload = json.dumps(message).encode()
    checksum = calculate_checksum(payload)
    return checksum + payload

def extract_and_verify(data):
    """Extract payload and verify checksum"""
    if len(data) < 4:
        return None, False
    
    checksum = data[:4]
    payload = data[4:]
    
    if verify_checksum(payload, checksum):
        return json.loads(payload.decode()), True
    return None, False

def create_signed_message(message_type, payload):
    """Create a signed message with checksum"""
    message = {
        "type": message_type,
        "payload": payload,
        "version": 1
    }
    return add_checksum(message)

def validate_message(data):
    """Validate incoming message with checksum"""
    try:
        message, valid = extract_and_verify(data)
        if not valid:
            print(f"[WARN] Invalid checksum on incoming message")
            return None, False
        return message, True
    except Exception as e:
        print(f"[WARN] Message validation error: {e}")
        return None, False
