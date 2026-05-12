"""
AddrMan - Address Manager with Bucketing (Bitcoin Standard)
Prevents eclipse attacks by organizing peers into diverse buckets
"""

import hashlib
import time
from collections import defaultdict
from typing import List, Dict, Optional, Tuple

class AddrMan:
    """Bitcoin-style address manager with bucketing"""
    
    def __init__(self):
        # 256 buckets, 64 entries per bucket (Bitcoin standard)
        self.NEW_BUCKET_COUNT = 256
        self.NEW_BUCKET_SIZE = 64
        self.TRIED_BUCKET_COUNT = 256
        self.TRIED_BUCKET_SIZE = 64
        
        # New addresses (not yet connected)
        self.new = [set() for _ in range(self.NEW_BUCKET_COUNT)]
        
        # Tried addresses (successfully connected)
        self.tried = [set() for _ in range(self.TRIED_BUCKET_COUNT)]
        
        # All known addresses
        self.addr_info = {}  # address -> info
        self.total_peers = 0
    
    def _get_bucket(self, address, source_ip, is_new=True):
        """Determine which bucket an address belongs to"""
        data = f"{address}{source_ip}".encode()
        bucket_hash = hashlib.sha256(data).hexdigest()
        bucket_num = int(bucket_hash[:8], 16)
        
        if is_new:
            return bucket_num % self.NEW_BUCKET_COUNT
        else:
            return bucket_num % self.TRIED_BUCKET_COUNT
    
    def _get_bucket_position(self, address, bucket_num, is_new=True):
        """Get position within bucket"""
        data = f"{address}{bucket_num}".encode()
        pos_hash = hashlib.sha256(data).hexdigest()
        pos = int(pos_hash[:8], 16)
        
        if is_new:
            return pos % self.NEW_BUCKET_SIZE
        else:
            return pos % self.TRIED_BUCKET_SIZE
    
    def add_address(self, address, source_ip="0.0.0.0"):
        """Add a new address to the manager"""
        if address in self.addr_info:
            self.addr_info[address]["last_seen"] = time.time()
            return
        
        if not self._is_valid_address(address):
            return
        
        new_bucket = self._get_bucket(address, source_ip, is_new=True)
        tried_bucket = self._get_bucket(address, source_ip, is_new=False)
        new_pos = self._get_bucket_position(address, new_bucket, is_new=True)
        tried_pos = self._get_bucket_position(address, tried_bucket, is_new=False)
        
        self.addr_info[address] = {
            "address": address,
            "source": source_ip,
            "first_seen": time.time(),
            "last_seen": time.time(),
            "new_bucket": new_bucket,
            "new_pos": new_pos,
            "tried_bucket": tried_bucket,
            "tried_pos": tried_pos,
            "success_count": 0,
            "fail_count": 0
        }
        
        self._add_to_bucket(address, new_bucket, new_pos, is_new=True)
        self.total_peers += 1
    
    def _is_valid_address(self, address):
        return address.startswith(("http://", "https://"))
    
    def _add_to_bucket(self, address, bucket_num, position, is_new=True):
        bucket = self.new[bucket_num] if is_new else self.tried[bucket_num]
        
        if len(bucket) >= (self.NEW_BUCKET_SIZE if is_new else self.TRIED_BUCKET_SIZE):
            oldest = None
            oldest_time = time.time()
            for addr in bucket:
                info = self.addr_info.get(addr, {})
                last_seen = info.get("last_seen", 0)
                if last_seen < oldest_time:
                    oldest_time = last_seen
                    oldest = addr
            if oldest:
                bucket.discard(oldest)
        
        bucket.add(address)
    
    def mark_success(self, address):
        if address in self.addr_info:
            self.addr_info[address]["success_count"] += 1
            self.addr_info[address]["last_seen"] = time.time()
            
            info = self.addr_info[address]
            if info["success_count"] >= 3 and address in self.new[info["new_bucket"]]:
                self.new[info["new_bucket"]].discard(address)
                self.tried[info["tried_bucket"]].add(address)
    
    def mark_failure(self, address):
        if address in self.addr_info:
            self.addr_info[address]["fail_count"] += 1
            if self.addr_info[address]["fail_count"] >= 5:
                self.remove_address(address)
    
    def remove_address(self, address):
        if address in self.addr_info:
            info = self.addr_info[address]
            self.new[info["new_bucket"]].discard(address)
            self.tried[info["tried_bucket"]].discard(address)
            del self.addr_info[address]
            self.total_peers -= 1
    
    def get_peer_for_connection(self):
        """Get a diverse peer for connection (prevents eclipse attacks)"""
        candidates = []
        buckets_used = set()
        
        for bucket in range(self.TRIED_BUCKET_COUNT):
            if len(buckets_used) > 10:
                break
            if self.tried[bucket]:
                bucket_num = bucket % len(self.tried)
                if bucket_num not in buckets_used:
                    buckets_used.add(bucket_num)
                    for addr in self.tried[bucket]:
                        candidates.append(addr)
                        break
        
        if len(candidates) < 5:
            for bucket in range(self.NEW_BUCKET_COUNT):
                if len(buckets_used) > 20:
                    break
                if self.new[bucket]:
                    bucket_num = bucket % len(self.new)
                    if bucket_num not in buckets_used:
                        buckets_used.add(bucket_num)
                        for addr in self.new[bucket]:
                            candidates.append(addr)
                            break
        
        return candidates
    
    def get_stats(self):
        return {
            "total_peers": self.total_peers,
            "new_buckets_used": sum(1 for b in self.new if b),
            "tried_buckets_used": sum(1 for b in self.tried if b),
            "bucket_count": self.NEW_BUCKET_COUNT,
            "bucket_size": self.NEW_BUCKET_SIZE,
            "standard": "Bitcoin_AddrMan"
        }
