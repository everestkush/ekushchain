"""Event streaming via ZMQ and webhooks"""
import zmq
import json
import time
import threading
import requests
import logging

logger = logging.getLogger(__name__)

class EventStreamer:
    def __init__(self, zmq_port=28332, webhook_url=None):
        self.zmq_port = zmq_port
        self.webhook_url = webhook_url
        self.zmq_context = None
        self.zmq_socket = None
    
    def start(self):
        self.zmq_context = zmq.Context()
        self.zmq_socket = self.zmq_context.socket(zmq.PUB)
        self.zmq_socket.bind(f"tcp://*:{self.zmq_port}")
        logger.info(f"ZMQ event streamer started on port {self.zmq_port}")
    
    def publish_block(self, block_hash, block_height):
        event = {
            'type': 'block',
            'hash': block_hash,
            'height': block_height,
            'timestamp': time.time()
        }
        
        if self.zmq_socket:
            self.zmq_socket.send_multipart([b'block', json.dumps(event).encode()])
        
        if self.webhook_url:
            threading.Thread(target=self._send_webhook, args=(event,)).start()
        
        logger.debug(f"Published block event: {block_hash[:8]}")
    
    def publish_transaction(self, txid, outputs):
        event = {
            'type': 'transaction',
            'txid': txid,
            'outputs': outputs,
            'timestamp': time.time()
        }
        
        if self.zmq_socket:
            self.zmq_socket.send_multipart([b'tx', json.dumps(event).encode()])
        
        logger.debug(f"Published tx event: {txid[:8]}")
    
    def publish_reorg(self, old_tip, new_tip, depth):
        event = {
            'type': 'reorg',
            'old_tip': old_tip,
            'new_tip': new_tip,
            'depth': depth,
            'timestamp': time.time()
        }
        
        if self.zmq_socket:
            self.zmq_socket.send_multipart([b'reorg', json.dumps(event).encode()])
        
        logger.warning(f"Published reorg event: depth {depth}")
    
    def _send_webhook(self, event):
        try:
            requests.post(self.webhook_url, json=event, timeout=1)
        except Exception as e:
            logger.debug(f"Webhook failed: {e}")
    
    def stop(self):
        if self.zmq_socket:
            self.zmq_socket.close()
        if self.zmq_context:
            self.zmq_context.term()
        logger.info("Event streamer stopped")
