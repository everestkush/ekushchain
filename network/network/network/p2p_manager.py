"""P2P Manager for block sync"""
import threading
import time
import sqlite3
from .p2p.peer import PeerConnection

class P2PManager:
    def __init__(self, db_path="ekush_chain.db"):
        self.db_path = db_path
        self.peers = []
        self.seed_nodes = ["103.74.15.88:8333", "192.168.23.5:8333"]
        self.best_height = 0
        self.syncing = False
    
    def start(self):
        for seed in self.seed_nodes:
            host, port = seed.split(':')
            peer = PeerConnection(host, int(port), on_block=self._on_block)
            if peer.connect():
                self.peers.append(peer)
                print(f"Connected to seed: {seed}")
        threading.Thread(target=self._sync_loop, daemon=True).start()
    
    def _on_block(self, block_data):
        import json
        block = json.loads(block_data)
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT OR IGNORE INTO blocks (idx, hash, previous_hash, validator, timestamp) VALUES (?, ?, ?, ?, ?)",
                     (block['idx'], block['hash'], block['previous_hash'], block['validator'], block['timestamp']))
        conn.commit()
        conn.close()
    
    def _sync_loop(self):
        while True:
            if not self.syncing:
                self.syncing = True
                for peer in self.peers:
                    if peer.best_height > self.best_height:
                        self._sync_blocks(peer)
                self.syncing = False
            time.sleep(10)
    
    def _sync_blocks(self, peer):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT MAX(idx) FROM blocks")
        current = cur.fetchone()[0] or 0
        conn.close()
        
        for height in range(current + 1, peer.best_height + 1):
            print(f"Syncing block {height}")
            # Request block from peer
            # This would use getdata message
    
    def broadcast_block(self, block):
        for peer in self.peers:
            peer.send_block(block)
