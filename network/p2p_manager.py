import threading
import time
import sqlite3
from p2p.peer import PeerConnection

class P2PManager:
    def __init__(self, db_path="ekush_chain.db"):
        self.db_path = db_path
        self.peers = []
        self.seed_nodes = ["103.74.15.88:8333"]
    
    def start(self):
        for seed in self.seed_nodes:
            host, port = seed.split(':')
            peer = PeerConnection(host, int(port), on_block=self._on_block)
            if peer.connect():
                self.peers.append(peer)
                print(f"Connected to seed: {seed}")
    
    def _on_block(self, block):
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT OR IGNORE INTO blocks (idx, hash, previous_hash, validator, timestamp) VALUES (?, ?, ?, ?, ?)",
                     (block['idx'], block['hash'], block['previous_hash'], block['validator'], block['timestamp']))
        conn.commit()
        conn.close()
        print(f"Synced block {block['idx']}")
    
    def broadcast_block(self, block):
        for peer in self.peers:
            try:
                peer.send_block(block)
            except:
                pass
