"""Bitcoin-style P2P Protocol for EverestKush"""
import struct
import hashlib
import time
import json
from enum import Enum

class MessageType(Enum):
    VERSION = 0
    VERACK = 1
    ADDR = 2
    INV = 3
    GETDATA = 4
    GETBLOCKS = 5
    GETHEADERS = 6
    TX = 7
    BLOCK = 8
    HEADERS = 9
    PING = 10
    PONG = 11
    REJECT = 12

class P2PMessage:
    MAGIC_BYTES = b'\x88\x88\x88\x88'  # EKUSH magic
    
    @staticmethod
    def serialize(cmd, payload):
        cmd_bytes = cmd.value.to_bytes(1, 'little')
        length = len(payload).to_bytes(4, 'little')
        checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
        return P2PMessage.MAGIC_BYTES + cmd_bytes + length + checksum + payload
    
    @staticmethod
    def deserialize(data):
        if len(data) < 10:
            return None
        if data[:4] != P2PMessage.MAGIC_BYTES:
            return None
        cmd = int.from_bytes(data[4:5], 'little')
        length = int.from_bytes(data[5:9], 'little')
        if len(data) < 9 + length:
            return None
        payload = data[9:9+length]
        return cmd, payload

class VersionMessage:
    """version handshake message"""
    def __init__(self, version=70015, height=0, user_agent="/EverestKush:2.0.0/"):
        self.version = version
        self.height = height
        self.user_agent = user_agent
        self.nonce = int(time.time())
        self.timestamp = int(time.time())
        self.start_height = height
    
    def serialize(self):
        payload = struct.pack('<I', self.version)
        payload += struct.pack('<Q', self.timestamp)
        payload += struct.pack('<Q', self.nonce)
        payload += struct.pack('<I', self.start_height)
        ua_bytes = self.user_agent.encode()
        payload += struct.pack('<B', len(ua_bytes)) + ua_bytes
        return payload
    
    @staticmethod
    def deserialize(payload):
        version = struct.unpack('<I', payload[:4])[0]
        timestamp = struct.unpack('<Q', payload[4:12])[0]
        nonce = struct.unpack('<Q', payload[12:20])[0]
        height = struct.unpack('<I', payload[20:24])[0]
        ua_len = payload[24]
        user_agent = payload[25:25+ua_len].decode()
        return VersionMessage(version, height, user_agent)

class HeadersMessage:
    """headers response for getheaders"""
    def __init__(self, headers):
        self.headers = headers
    
    def serialize(self):
        payload = struct.pack('<I', len(self.headers))
        for h in self.headers:
            payload += h.to_bytes(32, 'big')
        return payload

class BlockMessage:
    """full block message"""
    def __init__(self, block_data):
        self.block_data = block_data
    
    def serialize(self):
        return json.dumps(self.block_data).encode()
