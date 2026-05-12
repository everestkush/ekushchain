import os
"""Coin control - User selects which UTXOs to spend"""
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class CoinControl:
    """UTXO selection and coin control for transactions"""
    
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")):
        self.db_path = db_path
        self.selected_utxos: List[Dict] = []
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS utxos (
                outpoint TEXT PRIMARY KEY,
                address TEXT,
                amount INTEGER,
                script_pubkey TEXT,
                block_height INTEGER,
                is_spent INTEGER DEFAULT 0,
                is_frozen INTEGER DEFAULT 0,
                created_at INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    
    def list_utxos(self, address: Optional[str] = None) -> List[Dict]:
        """List all available UTXOs for an address"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        if address:
            cursor.execute('''
                SELECT outpoint, amount, address, block_height, is_frozen
                FROM utxos 
                WHERE address = ? AND is_spent = 0
                ORDER BY amount ASC
            ''', (address,))
        else:
            cursor.execute('''
                SELECT outpoint, amount, address, block_height, is_frozen
                FROM utxos 
                WHERE is_spent = 0
                ORDER BY amount ASC
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "outpoint": row[0],
                "amount": row[1],
                "address": row[2],
                "block_height": row[3],
                "is_frozen": bool(row[4])
            }
            for row in results
        ]
    
    def select_utxos(self, outpoints: List[str]) -> Dict:
        """Select specific UTXOs for spending"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        selected = []
        total_amount = 0
        
        for outpoint in outpoints:
            cursor.execute('''
                SELECT outpoint, amount, address, is_frozen, is_spent
                FROM utxos WHERE outpoint = ?
            ''', (outpoint,))
            row = cursor.fetchone()
            
            if not row:
                continue
            
            if row[3] == 1:  # is_frozen
                continue
            
            if row[4] == 1:  # is_spent
                continue
            
            selected.append({
                "outpoint": row[0],
                "amount": row[1],
                "address": row[2]
            })
            total_amount += row[1]
        
        conn.close()
        
        self.selected_utxos = selected
        
        return {
            "selected_count": len(selected),
            "total_amount": total_amount,
            "utxos": selected
        }
    
    def auto_select(self, target_amount: int, address: Optional[str] = None) -> Dict:
        """Automatically select UTXOs to reach target amount"""
        utxos = self.list_utxos(address)
        
        # Filter out frozen UTXOs
        available = [u for u in utxos if not u["is_frozen"]]
        
        # Sort by amount (smallest first for coin selection)
        available.sort(key=lambda x: x["amount"])
        
        selected = []
        total = 0
        
        for utxo in available:
            if total >= target_amount:
                break
            selected.append(utxo["outpoint"])
            total += utxo["amount"]
        
        if total < target_amount:
            return {
                "success": False,
                "error": "Insufficient funds",
                "available": sum(u["amount"] for u in available),
                "required": target_amount
            }
        
        return self.select_utxos(selected)
    
    def freeze_utxo(self, outpoint: str) -> Dict:
        """Freeze a UTXO (prevent it from being spent)"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('UPDATE utxos SET is_frozen = 1 WHERE outpoint = ?', (outpoint,))
        conn.commit()
        conn.close()
        return {"success": True, "outpoint": outpoint, "frozen": True}
    
    def unfreeze_utxo(self, outpoint: str) -> Dict:
        """Unfreeze a UTXO"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('UPDATE utxos SET is_frozen = 0 WHERE outpoint = ?', (outpoint,))
        conn.commit()
        conn.close()
        return {"success": True, "outpoint": outpoint, "frozen": False}
    
    def get_selected(self) -> Dict:
        """Get currently selected UTXOs"""
        return {
            "count": len(self.selected_utxos),
            "total_amount": sum(u["amount"] for u in self.selected_utxos),
            "utxos": self.selected_utxos
        }
    
    def clear_selected(self) -> Dict:
        """Clear selected UTXOs"""
        self.selected_utxos = []
        return {"success": True, "cleared": True}
    
    def get_stats(self) -> Dict:
        """Get coin control statistics"""
        utxos = self.list_utxos()
        frozen_count = len([u for u in utxos if u["is_frozen"]])
        total_amount = sum(u["amount"] for u in utxos)
        
        return {
            "total_utxos": len(utxos),
            "frozen_utxos": frozen_count,
            "total_amount": total_amount,
            "selected_count": len(self.selected_utxos),
            "selected_amount": sum(u["amount"] for u in self.selected_utxos),
            "coin_control_enabled": True
        }

coin_control = CoinControl()
