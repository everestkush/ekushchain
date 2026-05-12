"""Dandelion++ privacy protocol (BIP156) - Hide transaction origin IP"""
import time
import random
import threading
from collections import defaultdict
from typing import Set, Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class DandelionPP:
    """Dandelion++ transaction privacy protocol"""
    
    # Phases
    PHASE_STEM = "stem"
    PHASE_FLUFF = "fluff"
    
    def __init__(self, stem_probability=0.9, fluff_probability=0.1):
        self.stem_probability = stem_probability  # 90% chance to stay in stem
        self.fluff_probability = fluff_probability  # 10% chance to fluff
        self.stem_peers: Dict[str, str] = {}  # txid -> peer_id
        self.pending_txs: Dict[str, float] = {}  # txid -> timestamp
        self.stem_timeout = 120  # seconds
        self.epoch_length = 10  # seconds
    
    def should_stem(self) -> bool:
        """Determine if transaction should enter stem phase"""
        return random.random() < self.stem_probability
    
    def select_stem_peer(self, available_peers: List[str]) -> Optional[str]:
        """Select a random peer for stem phase"""
        if not available_peers:
            return None
        return random.choice(available_peers)
    
    def add_transaction(self, txid: str, peer_id: str) -> str:
        """Add transaction and determine phase"""
        phase = self.PHASE_STEM if self.should_stem() else self.PHASE_FLUFF
        
        if phase == self.PHASE_STEM:
            self.stem_peers[txid] = peer_id
            self.pending_txs[txid] = time.time()
            logger.info(f"TX {txid[:8]} entering STEM phase via peer {peer_id}")
        else:
            logger.info(f"TX {txid[:8]} entering FLUFF phase (direct broadcast)")
        
        return phase
    
    def forward_stem(self, txid: str, current_peer: str, available_peers: List[str]) -> Optional[str]:
        """Forward stem transaction to next peer"""
        if txid not in self.stem_peers:
            return None
        
        # Check if timeout
        if time.time() - self.pending_txs.get(txid, 0) > self.stem_timeout:
            self.fluff_transaction(txid)
            return None
        
        # Decide to fluff or continue stem
        if random.random() < self.fluff_probability:
            self.fluff_transaction(txid)
            return None
        
        # Continue stem to another peer
        other_peers = [p for p in available_peers if p != current_peer]
        if other_peers:
            next_peer = random.choice(other_peers)
            self.stem_peers[txid] = next_peer
            logger.info(f"TX {txid[:8]} forwarded to {next_peer}")
            return next_peer
        
        self.fluff_transaction(txid)
        return None
    
    def fluff_transaction(self, txid: str) -> None:
        """Broadcast transaction to all peers (fluff phase)"""
        if txid in self.stem_peers:
            del self.stem_peers[txid]
        if txid in self.pending_txs:
            del self.pending_txs[txid]
        logger.info(f"TX {txid[:8]} entered FLUFF phase - broadcasting to all peers")
    
    def get_stats(self) -> Dict:
        """Get Dandelion++ statistics"""
        return {
            "stem_phase_txs": len(self.stem_peers),
            "pending_txs": len(self.pending_txs),
            "stem_probability": self.stem_probability,
            "fluff_probability": self.fluff_probability,
            "stem_timeout": self.stem_timeout,
            "privacy_enabled": True
        }

# Global instance
dandelion = DandelionPP()
