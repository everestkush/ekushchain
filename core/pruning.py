import os
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import logging

logger = logging.getLogger(__name__)

class PruningManager:
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), prune_after=288):
        self.db_path = db_path
        self.prune_after = prune_after
    
    def prune_old_blocks(self, current_height: int):
        prune_below = current_height - self.prune_after
        if prune_below < 0:
            return
        
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute("SELECT hash, idx FROM blocks WHERE idx < ? AND is_pruned=0", (prune_below,))
        to_prune = cursor.fetchall()
        
        for block_hash, height in to_prune:
            cursor.execute("DELETE FROM blocks WHERE hash=?", (block_hash,))
            cursor.execute("DELETE FROM block_txs WHERE block_hash=?", (block_hash,))
            cursor.execute("INSERT INTO pruned_blocks (hash, height) VALUES (?, ?)", (block_hash, height))
        
        if to_prune:
            cursor.execute("VACUUM")
            logger.info(f"Pruned {len(to_prune)} blocks")
        
        conn.commit()
        conn.close()
    
    def enable_utxo_only_mode(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS blocks")
        cursor.execute("DROP TABLE IF EXISTS block_txs")
        cursor.execute("VACUUM")
        conn.commit()
        conn.close()
        logger.info("UTXO-only mode enabled")
