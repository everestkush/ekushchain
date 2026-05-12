"""Peer connection management"""
import socket
import threading
import time
from .protocol import P2PMessage, MessageType, VersionMessage

class PeerConnection:
    def __init__(self, host, port, on_block=None, on_tx=None):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.version_received = False
        self.verack_sent = False
        self.best_height = 0
        self.on_block = on_block
        self.on_tx = on_tx
    
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self._send_version()
            threading.Thread(target=self._receive_loop, daemon=True).start()
            return True
        except Exception as e:
            print(f"Failed to connect to {self.host}:{self.port} - {e}")
            return False
    
    def _send_version(self):
        vmsg = VersionMessage(height=0)
        payload = vmsg.serialize()
        data = P2PMessage.serialize(MessageType.VERSION, payload)
        self.socket.send(data)
    
    def _receive_loop(self):
        buffer = b''
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                buffer += data
                while True:
                    result = P2PMessage.deserialize(buffer)
                    if not result:
                        break
                    cmd, payload = result
                    buffer = buffer[9+len(payload):]
                    self._handle_message(cmd, payload)
            except Exception as e:
                print(f"Receive error: {e}")
                break
        self.connected = False
    
    def _handle_message(self, cmd, payload):
        if cmd == MessageType.VERSION.value:
            vmsg = VersionMessage.deserialize(payload)
            self.best_height = vmsg.start_height
            self._send_verack()
        elif cmd == MessageType.VERACK.value:
            self.verack_sent = True
        elif cmd == MessageType.BLOCK.value:
            if self.on_block:
                self.on_block(payload)
        elif cmd == MessageType.TX.value:
            if self.on_tx:
                self.on_tx(payload)
    
    def _send_verack(self):
        data = P2PMessage.serialize(MessageType.VERACK, b'')
        self.socket.send(data)
    
    def send_block(self, block_data):
        payload = BlockMessage(block_data).serialize()
        data = P2PMessage.serialize(MessageType.BLOCK, payload)
        self.socket.send(data)
    
    def close(self):
        self.connected = False
        if self.socket:
            self.socket.close()
