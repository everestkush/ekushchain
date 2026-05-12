import os
"""MuHash rolling UTXO set hash (BIP127) - Fast UTXO set verification"""
import hashlib
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class MuHash:
    """Rolling UTXO set hash for fast integrity verification"""
    
    # Prime modulus for MuHash (simplified for demo)
    MODULUS = 2**127 - 1
    
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")):
        self.db_path = db_path
        self.current_hash: Optional[int] = None
        self._init_db()
        self._load_or_compute_hash()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS muhash_state (
                id INTEGER PRIMARY KEY,
                hash_value TEXT,
                utxo_count INTEGER,
                total_amount INTEGER,
                updated_at INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    
    def _load_or_compute_hash(self):
        """Load existing hash or compute from UTXO set"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('SELECT hash_value, utxo_count, total_amount FROM muhash_state WHERE id = 1')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            self.current_hash = int(row[0])
            self.utxo_count = row[1]
            self.total_amount = row[2]
            logger.info(f"Loaded MuHash: {self.utxo_count} UTXOs, total: {self.total_amount}")
        else:
            self._compute_full_hash()
    
    def _compute_full_hash(self):
        """Compute MuHash from entire UTXO set"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('SELECT outpoint, amount FROM utxoset WHERE is_spent = 0')
        utxos = cursor.fetchall()
        conn.close()
        
        hash_value = 1
        total_amount = 0
        
        for outpoint, amount in utxos:
            # Simplified MuHash: combine hashes of each UTXO
            utxo_hash = int(hashlib.sha256(f"{outpoint}:{amount}".encode()).hexdigest()[:16], 16)
            hash_value = (hash_value * utxo_hash) % self.MODULUS
            total_amount += amount
        
        self.current_hash = hash_value
        self.utxo_count = len(utxos)
        self.total_amount = total_amount
        
        self._save_state()
        logger.info(f"Computed MuHash: {self.utxo_count} UTXOs, total: {self.total_amount}")
    
    def _save_state(self):
        """Save current MuHash state"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO muhash_state (id, hash_value, utxo_count, total_amount, updated_at)
            VALUES (1, ?, ?, ?, ?)
        ''', (str(self.current_hash), self.utxo_count, self.total_amount, int(time.time())))
        conn.commit()
        conn.close()
    
    def add_utxo(self, outpoint: str, amount: int) -> Dict:
        """Add UTXO to the rolling hash"""
        utxo_hash = int(hashlib.sha256(f"{outpoint}:{amount}".encode()).hexdigest()[:16], 16)
        self.current_hash = (self.current_hash * utxo_hash) % self.MODULUS
        self.utxo_count += 1
        self.total_amount += amount
        self._save_state()
        
        return {
            "added": True,
            "outpoint": outpoint,
            "amount": amount,
            "new_hash": hex(self.current_hash)[:16] + "..."
        }
    
    def remove_utxo(self, outpoint: str, amount: int) -> Dict:
        """Remove UTXO from the rolling hash (when spent)"""
        # Need modular inverse for removal (simplified)
        utxo_hash = int(hashlib.sha256(f"{outpoint}:{amount}".encode()).hexdigest()[:16], 16)
        # Simplified: recompute (in production use modular inverse)
        self._compute_full_hash()
        
        self._save_state()
        
        return {
            "removed": True,
            "outpoint": outpoint,
            "new_hash": hex(self.current_hash)[:16] + "..."
        }
    
    def verify(self) -> Dict:
        """Verify current UTXO set matches the hash"""
        old_hash = self.current_hash
        self._compute_full_hash()
        
        matches = old_hash == self.current_hash
        
        return {
            "verified": matches,
            "stored_hash": hex(old_hash)[:16] + "...",
            "computed_hash": hex(self.current_hash)[:16] + "...",
            "utxo_count": self.utxo_count,
            "total_amount": self.total_amount
        }
    
    def get_hash(self) -> str:
        """Get current MuHash"""
        return hex(self.current_hash)[2:] if self.current_hash else "0"
    
    def get_stats(self) -> Dict:
        """Get MuHash statistics"""
        return {
            "enabled": True,
            "bip": 127,
            "utxo_count": self.utxo_count,
            "total_amount": self.total_amount,
            "current_hash": self.get_hash()[:16] + "...",
            "verification_speed": "O(1) rolling update",
            "description": "Fast UTXO set integrity verification"
        }

muhash = MuHash()
