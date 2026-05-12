"""
Mempool manager with priority queue and persistence
"""
import sqlite3
import heapq
import time
import json
from typing import List, Any
from dataclasses import dataclass, field

@dataclass(order=True)
class MempoolEntry:
    """Entry in mempool with fee-based priority"""
    fee_per_byte: float
    timestamp: float = field(compare=False)
    tx_hash: str = field(compare=False)
    transaction: Any = field(compare=False)

class Mempool:
    """Priority queue mempool with persistence"""
    
    MAX_SIZE = 10000
    
    def __init__(self, db_path: str = "/home/kushal/everestkush/ekush_chain.db"):
        self.db_path = db_path
        self._queue = []
        self._tx_map = {}
        self._init_db()
        self._load_persisted()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mempool (
                tx_hash TEXT PRIMARY KEY,
                transaction_data TEXT,
                fee_per_byte REAL,
                timestamp INTEGER
            )
        """)
        conn.commit()
        conn.close()
    
    def _load_persisted(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        rows = conn.execute("SELECT tx_hash, transaction_data, fee_per_byte FROM mempool").fetchall()
        conn.close()
        
        from core.transaction import EKUSHTransaction
        for tx_hash, tx_data, fee_per_byte in rows:
            data = json.loads(tx_data)
            tx = EKUSHTransaction(
                sender=data['sender'],
                recipient=data['recipient'],
                amount=data['amount'],
                fee=data['fee']
            )
            tx.txid = tx_hash
            entry = MempoolEntry(
                fee_per_byte=fee_per_byte,
                timestamp=time.time(),
                tx_hash=tx_hash,
                transaction=tx
            )
            heapq.heappush(self._queue, entry)
            self._tx_map[tx_hash] = entry
        
        print(f"[BLOCK] Loaded {len(self._queue)} mempool transactions")
    
    def add_transaction(self, tx) -> bool:
        tx_hash = tx.calculate_hash()
        if tx_hash in self._tx_map:
            return False
        
        tx_size = len(json.dumps(tx.to_dict()))
        fee_per_byte = tx.fee / max(1, tx_size)
        
        entry = MempoolEntry(
            fee_per_byte=fee_per_byte,
            timestamp=time.time(),
            tx_hash=tx_hash,
            transaction=tx
        )
        
        heapq.heappush(self._queue, entry)
        self._tx_map[tx_hash] = entry
        
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("INSERT OR REPLACE INTO mempool (tx_hash, transaction_data, fee_per_byte, timestamp) VALUES (?, ?, ?, ?)",
                     (tx_hash, json.dumps(tx.to_dict()), fee_per_byte, int(time.time())))
        conn.commit()
        conn.close()
        
        while len(self._queue) > self.MAX_SIZE:
            self._pop_lowest()
        
        return True
    
    def _pop_lowest(self):
        if not self._queue:
            return None
        entry = heapq.heappop(self._queue)
        del self._tx_map[entry.tx_hash]
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("DELETE FROM mempool WHERE tx_hash = ?", (entry.tx_hash,))
        conn.commit()
        conn.close()
        return entry
    
    def get_top_transactions(self, limit: int = 100) -> List:
        if not self._queue:
            return []
        sorted_entries = sorted(self._queue, reverse=True)[:limit]
        return [e.transaction for e in sorted_entries]
    
    def remove_transaction(self, tx_hash: str):
        if tx_hash not in self._tx_map:
            return
        del self._tx_map[tx_hash]
        self._queue = [e for e in self._queue if e.tx_hash != tx_hash]
        heapq.heapify(self._queue)
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("DELETE FROM mempool WHERE tx_hash = ?", (tx_hash,))
        conn.commit()
        conn.close()
    
    def size(self) -> int:
        return len(self._queue)
    
    def get_transaction(self, tx_hash: str):
        entry = self._tx_map.get(tx_hash)
        return entry.transaction if entry else None
    
    def clear(self):
        self._queue = []
        self._tx_map = {}
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("DELETE FROM mempool")
        conn.commit()
        conn.close()
