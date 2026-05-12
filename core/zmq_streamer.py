import zmq
import json
import time
import threading

class ZMQStreamer:
    def __init__(self, port=28332):
        self.port = port
        self.context = None
        self.socket = None
        self.running = False
    
    def start(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://0.0.0.0:{self.port}")
        self.running = True
        print(f"ZMQ streamer on port {self.port}")
        return self
    
    def publish_block(self, block_hash, block_height):
        if not self.running:
            return
        message = {
            "type": "block",
            "hash": block_hash,
            "height": block_height,
            "timestamp": int(time.time())
        }
        self.socket.send_multipart([b"blocks", json.dumps(message).encode()])
    
    def publish_tx(self, txid):
        if not self.running:
            return
        message = {"type": "tx", "txid": txid, "timestamp": int(time.time())}
        self.socket.send_multipart([b"transactions", json.dumps(message).encode()])
    
    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
