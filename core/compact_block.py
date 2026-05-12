"""
Compact Block Relay (BIP152) - Bitcoin Standard
90% bandwidth reduction for block propagation
"""

import hashlib
import struct
from typing import List, Dict, Optional
from collections import defaultdict

class CompactBlock:
    """Compact block representation for BIP152"""
    
    def __init__(self, block, mempool):
        self.block = block
        self.mempool = mempool
        self.short_ids = []
        self.prefilled_txns = []
        
    def create_compact_block(self):
        """Create compact block (headers + short IDs)"""
        # Block header (80 bytes)
        header = {
            "index": self.block.index,
            "hash": self.block.hash,
            "previous_hash": self.block.previous_hash,
            "merkle_root": self.block.merkle_root,
            "timestamp": self.block.timestamp,
            "difficulty": self.block.difficulty,
            "nonce": self.block.nonce
        }
        
        # Generate short IDs for transactions
        for tx in self.block.transactions:
            tx_hash = tx.calculate_hash()
            short_id = self._calculate_short_id(tx_hash)
            self.short_ids.append(short_id)
        
        return {
            "header": header,
            "short_ids": self.short_ids,
            "prefilled_txns": self.prefilled_txns,
            "total_txns": len(self.block.transactions)
        }
    
    def _calculate_short_id(self, tx_hash):
        """Calculate 6-byte short ID from transaction hash (BIP152)"""
        # Take first 6 bytes of double SHA256
        double_hash = hashlib.sha256(hashlib.sha256(tx_hash.encode()).digest()).digest()
        return struct.unpack('<Q', double_hash[:8])[0] & 0xFFFFFFFFFFFF
    
    def reconstruct_block(self, compact_data, mempool):
        """Reconstruct full block from compact data"""
        transactions = []
        missing_txns = []
        
        # Get prefilled transactions
        for prefilled in compact_data.get("prefilled_txns", []):
            transactions.append(prefilled)
        
        # Try to find transactions by short ID in mempool
        for short_id in compact_data.get("short_ids", []):
            found = False
            for tx in mempool:
                tx_hash = tx.calculate_hash()
                if self._calculate_short_id(tx_hash) == short_id:
                    transactions.append(tx)
                    found = True
                    break
            if not found:
                missing_txns.append(short_id)
        
        return transactions, missing_txns


class CompactBlockRelay:
    """Handle compact block relay between nodes"""
    
    def __init__(self):
        self.pending_compact_blocks = {}
        self.requested_blocks = set()
    
    def should_send_compact(self, block, peer_mempool):
        """Determine if we should send compact block instead of full"""
        # If peer has most transactions in mempool, send compact
        matching = 0
        for tx in block.transactions:
            tx_hash = tx.calculate_hash()
            for peer_tx in peer_mempool:
                if peer_tx.calculate_hash() == tx_hash:
                    matching += 1
                    break
        
        # Send compact if peer has >50% of transactions
        return matching > len(block.transactions) / 2
    
    def send_compact_block(self, block, peer, peer_mempool):
        """Send compact block to peer"""
        if not self.should_send_compact(block, peer_mempool):
            return None
        
        compact = CompactBlock(block, peer_mempool)
        return compact.create_compact_block()
    
    def receive_compact_block(self, compact_data, mempool):
        """Receive and reconstruct compact block"""
        compact = CompactBlock(None, mempool)
        transactions, missing = compact.reconstruct_block(compact_data, mempool)
        
        return {
            "transactions": transactions,
            "missing_count": len(missing),
            "reconstructed": len(missing) == 0
        }
    
    def request_missing_transactions(self, missing_short_ids):
        """Request missing transactions from peer"""
        return {
            "type": "getblocktxn",
            "short_ids": missing_short_ids
        }
