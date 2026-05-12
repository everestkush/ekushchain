import requests
import json
import threading
import time
from flask import Flask, jsonify, request
from collections import defaultdict
from core.addrmgr import AddrMan
from core.checksum import validate_message, create_signed_message, calculate_checksum

class PeerScore:
    """Track peer behavior and score (Bitcoin standard)"""
    
    def __init__(self, peer_url):
        self.peer_url = peer_url
        self.score = 100
        self.valid_blocks = 0
        self.invalid_blocks = 0
        self.valid_tx = 0
        self.invalid_tx = 0
        self.latency = 0
        self.last_seen = time.time()
        self.banned = False
        self.ban_reason = None
    
    def record_valid_block(self):
        self.valid_blocks += 1
        self.score = min(100, self.score + 1)
        self.last_seen = time.time()
    
    def record_invalid_block(self, reason):
        self.invalid_blocks += 1
        self.score -= 20
        self.last_seen = time.time()
        if self.score <= 0:
            self.banned = True
            self.ban_reason = f"Invalid block: {reason}"
    
    def record_valid_tx(self):
        self.valid_tx += 1
        self.score = min(100, self.score + 0.5)
        self.last_seen = time.time()
    
    def record_invalid_tx(self, reason):
        self.invalid_tx += 1
        self.score -= 10
        self.last_seen = time.time()
        if self.score <= 0:
            self.banned = True
            self.ban_reason = f"Invalid transaction: {reason}"
    
    def record_latency(self, latency_ms):
        self.latency = latency_ms
        if latency_ms > 5000:
            self.score -= 1
        elif latency_ms < 500:
            self.score = min(100, self.score + 0.5)
    
    def record_timeout(self):
        self.score -= 2
        if self.score <= 0:
            self.banned = True
            self.ban_reason = "Repeated timeouts"
    
    def get_info(self):
        return {
            "peer_url": self.peer_url,
            "score": self.score,
            "banned": self.banned,
            "ban_reason": self.ban_reason,
            "valid_blocks": self.valid_blocks,
            "invalid_blocks": self.invalid_blocks,
            "valid_tx": self.valid_tx,
            "invalid_tx": self.invalid_tx,
            "latency_ms": self.latency,
            "last_seen": self.last_seen
        }


class EKUSHNode:
    def __init__(self, host, port, chain, storage_funcs):
        self.host = host
        self.port = port
        self.chain = chain
        self.peers = set()
        self.save_chain = storage_funcs['save']
        self.node_id = f"{host}:{port}"
        self.use_https = True
        self.peer_scores = {}
        self.addrman = AddrMan()
        self.MAX_PEERS = 125
        self.MAX_OUTBOUND = 8
        self.MAX_INBOUND = 117
        print(f"Node initialized: {self.node_id} (HTTPS mode: {self.use_https})")

    def _get_peer_url(self, peer):
        if peer.startswith("http://"):
            peer = peer.replace("http://", "https://")
        if not peer.startswith("https://"):
            peer = f"https://{peer}"
        return peer.rstrip('/')

    def _get_peer_score(self, peer_url):
        if peer_url not in self.peer_scores:
            self.peer_scores[peer_url] = PeerScore(peer_url)
        return self.peer_scores[peer_url]

    def is_peer_banned(self, peer_url):
        score_obj = self._get_peer_score(peer_url)
        return score_obj.banned

    def add_peer(self, peer_url):
        peer_url = self._get_peer_url(peer_url)
        
        if self.is_peer_banned(peer_url):
            print(f"🚫 Peer {peer_url} is banned, rejecting connection")
            return False
        
        if len(self.peers) >= self.MAX_PEERS:
            self._evict_worst_peer()
        
        self.peers.add(peer_url)
        self.addrman.add_address(peer_url, self.host)
        print(f"Peer added: {peer_url}")
        return True

    def _evict_worst_peer(self):
        if not self.peer_scores:
            return
        worst_peer = min(self.peer_scores, key=lambda p: self.peer_scores[p].score)
        self.peers.discard(worst_peer)
        print(f"🔌 Evicted peer {worst_peer} (score: {self.peer_scores[worst_peer].score})")

    def record_peer_behavior(self, peer_url, behavior, details=None):
        if self.is_peer_banned(peer_url):
            return
        
        score_obj = self._get_peer_score(peer_url)
        
        if behavior == "valid_block":
            score_obj.record_valid_block()
        elif behavior == "invalid_block":
            score_obj.record_invalid_block(details or "Unknown reason")
        elif behavior == "valid_tx":
            score_obj.record_valid_tx()
        elif behavior == "invalid_tx":
            score_obj.record_invalid_tx(details or "Unknown reason")
        elif behavior == "timeout":
            score_obj.record_timeout()
        
        if score_obj.banned:
            print(f"🚫 Peer {peer_url} has been BANNED! Reason: {score_obj.ban_reason}")
            self.peers.discard(peer_url)

    def broadcast_block(self, block):
        block_data = {
            "index": block.index,
            "hash": block.hash,
            "previous_hash": block.previous_hash,
            "validator": block.validator,
            "timestamp": block.timestamp,
            "nonce": block.nonce,
            "merkle_root": block.merkle_root,
            "transactions": [tx.to_dict() for tx in block.transactions]
        }
        
        # Add checksum to message
        signed_message = create_signed_message("block", block_data)
        
        print(f"📡 Broadcasting block #{block.index} to {len(self.peers)} peers")
        for peer in self.peers:
            if self.is_peer_banned(peer):
                continue
            try:
                start_time = time.time()
                peer_url = self._get_peer_url(peer)
                response = requests.post(
                    f"{peer_url}/p2p/block",
                    data=signed_message,
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=5,
                    verify=False
                )
                latency = (time.time() - start_time) * 1000
                self._get_peer_score(peer).record_latency(latency)
                print(f"✅ Block #{block.index} broadcast to {peer_url} - Status: {response.status_code} ({latency:.0f}ms)")
            except Exception as e:
                print(f"❌ Failed to reach peer {peer}: {e}")
                self.record_peer_behavior(peer, "timeout")

    def broadcast_transaction(self, tx):
        tx_data = tx.to_dict()
        tx_hash = tx.calculate_hash()[:16]
        
        # Add checksum to message
        signed_message = create_signed_message("transaction", tx_data)
        
        print(f"📡 Broadcasting transaction {tx_hash} to {len(self.peers)} peers")
        for peer in self.peers:
            if self.is_peer_banned(peer):
                continue
            try:
                start_time = time.time()
                peer_url = self._get_peer_url(peer)
                print(f"📡 Sending to {peer_url}...")
                response = requests.post(
                    f"{peer_url}/p2p/transaction",
                    data=signed_message,
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=5,
                    verify=False
                )
                latency = (time.time() - start_time) * 1000
                self._get_peer_score(peer).record_latency(latency)
                print(f"✅ Transaction {tx_hash} broadcast to {peer_url} - Status: {response.status_code} ({latency:.0f}ms)")
                if response.status_code == 200:
                    print(f"   Response: {response.json()}")
            except Exception as e:
                print(f"❌ Failed to reach peer {peer}: {e}")
                self.record_peer_behavior(peer, "timeout")

    def sync_with_peers(self):
        for peer in self.peers:
            if self.is_peer_banned(peer):
                continue
            try:
                peer_url = self._get_peer_url(peer)
                r = requests.get(f"{peer_url}/chain", timeout=10, verify=False)
                peer_chain = r.json()
                if peer_chain['length'] > len(self.chain.chain):
                    print(f"Peer {peer_url} has longer chain ({peer_chain['length']} blocks) — syncing...")
                    self._replace_chain(peer_chain['chain'])
                    self.record_peer_behavior(peer, "valid_block")
                else:
                    print(f"Our chain is up to date ({len(self.chain.chain)} blocks)")
            except Exception as e:
                print(f"Sync failed with {peer}: {e}")
                self.record_peer_behavior(peer, "timeout")

    def _replace_chain(self, chain_data):
        print(f"Chain replacement needed — implement full sync here")
        pass

    def ping_peers(self):
        alive = []
        dead = []
        for peer in self.peers:
            if self.is_peer_banned(peer):
                dead.append(peer)
                continue
            try:
                start_time = time.time()
                peer_url = self._get_peer_url(peer)
                r = requests.get(f"{peer_url}/p2p/ping", timeout=3, verify=False)
                latency = (time.time() - start_time) * 1000
                self._get_peer_score(peer).record_latency(latency)
                if r.status_code == 200:
                    alive.append(peer)
                    print(f"✅ Peer {peer_url} is alive ({latency:.0f}ms)")
            except Exception as e:
                dead.append(peer)
                print(f"❌ Peer {peer} is dead: {e}")
                self.record_peer_behavior(peer, "timeout")
        return {"alive": alive, "dead": dead}

    def get_peer_list(self):
        return list(self.peers)

    def get_peer_scores(self):
        result = {}
        for peer in self.peers:
            if peer in self.peer_scores:
                result[peer] = self.peer_scores[peer].get_info()
            else:
                result[peer] = {
                    "peer_url": peer,
                    "score": 100,
                    "banned": False,
                    "ban_reason": None,
                    "valid_blocks": 0,
                    "invalid_blocks": 0,
                    "valid_tx": 0,
                    "invalid_tx": 0,
                    "latency_ms": 0,
                    "last_seen": time.time()
                }
        return result
