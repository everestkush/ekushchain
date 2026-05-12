import os
"""3-tier UTXO cache - Memory -> SQLite -> Disk for optimal performance"""
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time
import threading
from collections import OrderedDict
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class UTXOCache:
    """3-tier UTXO cache with LRU memory cache"""
    
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), max_memory_cache=10000):
        self.db_path = db_path
        self.max_memory_cache = max_memory_cache
        self.memory_cache: OrderedDict = OrderedDict()  # LRU cache
        self.hits = 0
        self.misses = 0
        self._init_db()
        self._lock = threading.Lock()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS utxo_cache_sqlite (
                outpoint TEXT PRIMARY KEY,
                amount INTEGER,
                script_pubkey TEXT,
                block_height INTEGER,
                is_spent INTEGER DEFAULT 0,
                cached_at INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    
    def get(self, outpoint: str) -> Optional[Dict]:
        """Get UTXO from cache (memory -> SQLite -> disk)"""
        with self._lock:
            # Tier 1: Memory cache
            if outpoint in self.memory_cache:
                self.memory_cache.move_to_end(outpoint)
                self.hits += 1
                logger.debug(f"Cache HIT (memory): {outpoint[:16]}")
                return self.memory_cache[outpoint]
            
            # Tier 2: SQLite cache
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT amount, script_pubkey, block_height, is_spent 
                FROM utxo_cache_sqlite WHERE outpoint = ?
            ''', (outpoint,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                utxo = {
                    "outpoint": outpoint,
                    "amount": row[0],
                    "script_pubkey": row[1],
                    "block_height": row[2],
                    "is_spent": bool(row[3])
                }
                # Promote to memory cache
                self._add_to_memory(outpoint, utxo)
                self.hits += 1
                logger.debug(f"Cache HIT (SQLite): {outpoint[:16]}")
                return utxo
            
            # Tier 3: Disk (full DB scan)
            utxo = self._fetch_from_disk(outpoint)
            if utxo:
                self._add_to_sqlite_cache(outpoint, utxo)
                self._add_to_memory(outpoint, utxo)
                self.misses += 1
                logger.debug(f"Cache MISS (disk): {outpoint[:16]}")
                return utxo
            
            self.misses += 1
            return None
    
    def _fetch_from_disk(self, outpoint: str) -> Optional[Dict]:
        """Fetch UTXO from main database (disk tier)"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT amount, script_pubkey, block_height, is_spent 
            FROM utxoset WHERE outpoint = ?
        ''', (outpoint,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "outpoint": outpoint,
                "amount": row[0],
                "script_pubkey": row[1],
                "block_height": row[2],
                "is_spent": bool(row[3])
            }
        return None
    
    def _add_to_memory(self, outpoint: str, utxo: Dict):
        """Add UTXO to memory cache (LRU)"""
        if len(self.memory_cache) >= self.max_memory_cache:
            # Remove oldest
            oldest = next(iter(self.memory_cache))
            del self.memory_cache[oldest]
        
        self.memory_cache[outpoint] = utxo
        self.memory_cache.move_to_end(outpoint)
    
    def _add_to_sqlite_cache(self, outpoint: str, utxo: Dict):
        """Add UTXO to SQLite cache"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO utxo_cache_sqlite 
            (outpoint, amount, script_pubkey, block_height, is_spent, cached_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (outpoint, utxo["amount"], utxo["script_pubkey"], 
              utxo["block_height"], 1 if utxo["is_spent"] else 0, int(time.time())))
        conn.commit()
        conn.close()
    
    def set(self, outpoint: str, utxo: Dict):
        """Store UTXO in all cache tiers"""
        with self._lock:
            self._add_to_memory(outpoint, utxo)
            self._add_to_sqlite_cache(outpoint, utxo)
    
    def invalidate(self, outpoint: str):
        """Remove UTXO from all cache tiers (when spent)"""
        with self._lock:
            if outpoint in self.memory_cache:
                del self.memory_cache[outpoint]
            
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM utxo_cache_sqlite WHERE outpoint = ?', (outpoint,))
            conn.commit()
            conn.close()
    
    def get_stats(self) -> Dict:
        """Get cache performance statistics"""
        hit_rate = (self.hits / (self.hits + self.misses) * 100) if (self.hits + self.misses) > 0 else 0
        
        return {
            "tiers": ["Memory (L1)", "SQLite (L2)", "Disk (L3)"],
            "memory_cache_size": len(self.memory_cache),
            "max_memory_cache": self.max_memory_cache,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_enabled": True
        }

utxo_cache = UTXOCache()
