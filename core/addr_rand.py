"""Address announcement randomization - Prevent peer fingerprinting"""
import random
import time
from collections import defaultdict
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

class AddrRandomizer:
    """Randomize address announcements to prevent peer fingerprinting"""
    
    def __init__(self):
        self.peer_announcements: Dict[str, List[float]] = defaultdict(list)
        self.announcement_pool: Dict[str, Set[str]] = defaultdict(set)
        self.batch_size = 10
        self.announce_interval = 60  # seconds between announcements
    
    def add_address(self, peer_id: str, address: str) -> None:
        """Add address to announcement pool"""
        self.announcement_pool[peer_id].add(address)
        logger.debug(f"Added address {address} to pool for peer {peer_id}")
    
    def get_randomized_batch(self, peer_id: str, max_count: int = 10) -> List[str]:
        """Get randomized batch of addresses to announce"""
        addresses = list(self.announcement_pool.get(peer_id, set()))
        if not addresses:
            return []
        
        # Randomize order and select subset
        random.shuffle(addresses)
        batch_size = min(max_count, len(addresses))
        batch = addresses[:batch_size]
        
        # Record announcement time
        now = time.time()
        self.peer_announcements[peer_id].append(now)
        
        # Clean old announcements
        self._cleanup_old(peer_id)
        
        logger.info(f"Announcing {len(batch)} addresses to peer {peer_id}")
        return batch
    
    def _cleanup_old(self, peer_id: str) -> None:
        """Remove announcements older than interval"""
        cutoff = time.time() - self.announce_interval
        self.peer_announcements[peer_id] = [
            ts for ts in self.peer_announcements[peer_id] if ts > cutoff
        ]
    
    def should_announce(self, peer_id: str) -> bool:
        """Check if we should announce to this peer"""
        last_announce = self.peer_announcements[peer_id][-1] if self.peer_announcements[peer_id] else 0
        return time.time() - last_announce >= self.announce_interval
    
    def get_stats(self) -> Dict:
        """Get randomization statistics"""
        return {
            "total_peers": len(self.announcement_pool),
            "total_addresses": sum(len(addrs) for addrs in self.announcement_pool.values()),
            "batch_size": self.batch_size,
            "announce_interval": self.announce_interval,
            "randomization_enabled": True
        }

addr_randomizer = AddrRandomizer()
