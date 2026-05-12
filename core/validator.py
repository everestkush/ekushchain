import os
"""Validator management with 8,888 EKUSH minimum bond"""
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time
from typing import Dict

class ValidatorManager:
    MINIMUM_BOND = 8888
    MAX_VALIDATORS = 21
    
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS validators (
                address TEXT PRIMARY KEY,
                bonded_amount INTEGER,
                status TEXT DEFAULT 'pending',
                joined_at INTEGER,
                last_active INTEGER,
                slashed_amount INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def _get_balance(self, address: str) -> int:
        """Get balance from UTXO set for specific address"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        c = conn.cursor()
        

        try:
            c.execute('SELECT SUM(amount) FROM utxos WHERE address = ? AND is_spent = 0', (address,))
            row = c.fetchone()
            balance = row[0] if row and row[0] else 0
        except:
            balance = 0
        
        conn.close()
        return balance
    
    def can_become_validator(self, address: str) -> Dict:
        """Check if address meets validator requirements"""
        balance = self._get_balance(address)
        
        if balance < self.MINIMUM_BOND:
            return {
                "eligible": False,
                "reason": f"Need {self.MINIMUM_BOND} EKUSH (have {balance})",
                "required": self.MINIMUM_BOND,
                "current": balance
            }
        
        return {
            "eligible": True,
            "message": f"Ready to become validator with {balance} EKUSH"
        }
    
    def bond(self, address: str, amount: int) -> Dict:
        """Bond EKUSH to become validator"""
        if amount < self.MINIMUM_BOND:
            return {"success": False, "error": f"Minimum bond is {self.MINIMUM_BOND} EKUSH"}
        
        balance = self._get_balance(address)
        
        if balance < amount:
            return {"success": False, "error": f"Insufficient balance (have {balance}, need {amount})"}
        
        conn = sqlite3.connect(self.db_path, timeout=30)
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO validators (address, bonded_amount, status, joined_at, last_active)
            VALUES (?, ?, 'active', ?, ?)
        ''', (address, amount, int(time.time()), int(time.time())))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Validator bonded with {amount} EKUSH",
            "minimum_required": self.MINIMUM_BOND,
            "reward_rate": f"{DifficultyAdjustment().get_block_reward(height)/1000000:.4f} EKUSH per block (APR-based)"
        }
    
    def get_validator_count(self) -> int:
        conn = sqlite3.connect(self.db_path, timeout=30)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM validators WHERE status = "active"')
        count = c.fetchone()[0]
        conn.close()
        return count
    
    def can_start_mining(self, address: str) -> Dict:
        conn = sqlite3.connect(self.db_path, timeout=30)
        c = conn.cursor()
        c.execute('SELECT bonded_amount FROM validators WHERE address = ? AND status = "active"', (address,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return {"can_mine": False, "reason": "Not a validator. Bond 8,888 EKUSH first"}
        
        return {"can_mine": True, "bonded": row[0]}

validator_manager = ValidatorManager()
