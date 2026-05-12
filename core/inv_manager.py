"""INV / GETDATA message flow - Prevent duplicate block downloads"""
import time
import threading
from collections import defaultdict
from typing import Set, Dict, List
import logging

logger = logging.getLogger(__name__)

class InvManager:
    """Inventory manager for P2P message flow"""
    
    def __init__(self):
        self.requested_inv: Dict[str, float] = {}  # inv_hash -> timestamp
        self.received_inv: Set[str] = set()        # Already received
        self.peer_requests: Dict[str, Set[str]] = defaultdict(set)  # peer -> requested invs
        self.inv_timeout = 30  # seconds
    
    def add_inv(self, inv_hash: str, peer_id: str) -> bool:
        """Add inventory item, return True if new (not seen before)"""
        if inv_hash in self.received_inv:
            logger.debug(f"INV {inv_hash[:8]} already received, skipping")
            return False
        
        if inv_hash in self.requested_inv:
            age = time.time() - self.requested_inv[inv_hash]
            if age < self.inv_timeout:
                logger.debug(f"INV {inv_hash[:8]} already requested {age:.1f}s ago")
                return False
        
        self.requested_inv[inv_hash] = time.time()
        self.peer_requests[peer_id].add(inv_hash)
        logger.info(f"Added INV {inv_hash[:8]} from peer {peer_id}")
        return True
    
    def mark_received(self, inv_hash: str) -> None:
        """Mark inventory as received"""
        self.received_inv.add(inv_hash)
        if inv_hash in self.requested_inv:
            del self.requested_inv[inv_hash]
        logger.debug(f"Marked {inv_hash[:8]} as received")
    
    def get_peers_to_request_from(self, inv_hash: str) -> List[str]:
        """Get peers that haven't requested this inv yet"""
        peers = []
        for peer_id, requested in self.peer_requests.items():
            if inv_hash not in requested:
                peers.append(peer_id)
        return peers
    
    def cleanup_expired(self) -> int:
        """Remove expired requests"""
        now = time.time()
        expired = [h for h, ts in self.requested_inv.items() if now - ts > self.inv_timeout]
        for h in expired:
            del self.requested_inv[h]
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired INVs")
        return len(expired)
    
    def get_stats(self) -> Dict:
        """Get inventory manager statistics"""
        return {
            "pending_requests": len(self.requested_inv),
            "received_total": len(self.received_inv),
            "active_peers": len(self.peer_requests),
            "timeout_seconds": self.inv_timeout
        }

# Global instance
inv_manager = InvManager()

# Cleanup thread
def start_cleanup_thread():
    def cleanup_loop():
        while True:
            time.sleep(60)
            inv_manager.cleanup_expired()
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
    logger.info("INV cleanup thread started")

start_cleanup_thread()
