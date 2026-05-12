import os
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class DeepReorgManager:
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), max_depth=1000):
        self.db_path = db_path
        self.max_depth = max_depth
    
    def detect_and_recover(self, new_tip_hash: str, new_tip_height: int) -> Dict:
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute("SELECT hash, idx FROM blocks ORDER BY idx DESC LIMIT 1")
        current = cursor.fetchone()
        
        if not current:
            return {"reorg": False, "message": "No chain tip"}
        
        current_hash, current_height = current
        
        if current_hash == new_tip_hash:
            return {"reorg": False, "message": "Already on best chain"}
        
        fork_point = self._find_fork_point(new_tip_hash, cursor)
        
        if current_height - fork_point > self.max_depth:
            return {"reorg": False, "error": f"Reorg depth exceeds limit {self.max_depth}"}
        
        disconnected = self._disconnect_blocks(fork_point + 1, cursor)
        connected = self._connect_blocks(new_tip_hash, fork_point, cursor)
        
        conn.commit()
        conn.close()
        
        return {
            "reorg": True,
            "fork_height": fork_point,
            "disconnected": len(disconnected),
            "connected": len(connected),
            "new_height": new_tip_height
        }
    
    def _find_fork_point(self, block_hash: str, cursor) -> int:
        heights = set()
        current = block_hash
        while current:
            cursor.execute("SELECT idx, previous_hash FROM blocks WHERE hash=?", (current,))
            row = cursor.fetchone()
            if not row:
                break
            heights.add(row[0])
            current = row[1]
        
        cursor.execute("SELECT idx FROM blocks ORDER BY idx DESC")
        for row in cursor.fetchall():
            if row[0] in heights:
                return row[0]
        return 0
    
    def _disconnect_blocks(self, from_height: int, cursor) -> List[str]:
        disconnected = []
        cursor.execute("SELECT hash FROM blocks WHERE idx >= ?", (from_height,))
        for row in cursor.fetchall():
            cursor.execute("UPDATE blocks SET is_active=0 WHERE hash=?", (row[0],))
            disconnected.append(row[0])
        return disconnected
    
    def _connect_blocks(self, tip_hash: str, fork_height: int, cursor) -> List[str]:
        connected = []
        to_connect = []
        current = tip_hash
        while current:
            cursor.execute("SELECT idx, previous_hash FROM blocks WHERE hash=?", (current,))
            row = cursor.fetchone()
            if not row or row[0] <= fork_height:
                break
            to_connect.append(current)
            current = row[1]
        for blk_hash in reversed(to_connect):
            cursor.execute("UPDATE blocks SET is_active=1 WHERE hash=?", (blk_hash,))
            connected.append(blk_hash)
        return connected
