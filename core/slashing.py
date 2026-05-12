import os
"""Equivocation slashing - Penalize double-voting validators"""
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SlashingManager:
    """Handle validator slashing for equivocation (double-voting)"""
    
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS slashing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                validator TEXT NOT NULL,
                offense_type TEXT NOT NULL,
                block_height INTEGER,
                evidence TEXT,
                slash_amount INTEGER,
                timestamp INTEGER,
                processed INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validator_jail (
                validator TEXT PRIMARY KEY,
                jailed_until INTEGER,
                slash_count INTEGER DEFAULT 0,
                total_slashed INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def report_equivocation(self, validator: str, block_height: int, evidence: Dict) -> Dict:
        """Report a validator for double-voting"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        # Check if already slashed for this offense
        cursor.execute('''
            SELECT id FROM slashing_events 
            WHERE validator = ? AND block_height = ? AND offense_type = 'equivocation'
        ''', (validator, block_height))
        
        if cursor.fetchone():
            conn.close()
            return {"slashed": False, "reason": "Already reported"}
        
        # Calculate slash amount (10% of stake for first offense, increasing)
        cursor.execute('SELECT slash_count FROM validator_jail WHERE validator = ?', (validator,))
        row = cursor.fetchone()
        slash_count = row[0] if row else 0
        slash_percent = min(0.10 + (slash_count * 0.05), 0.50)  # 10%, 15%, 20%... max 50%
        
        # Record slashing event
        cursor.execute('''
            INSERT INTO slashing_events 
            (validator, offense_type, block_height, evidence, slash_amount, timestamp, processed)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (validator, 'equivocation', block_height, str(evidence), int(slash_percent * 100), int(time.time())))
        
        # Update or insert jail record
        jail_until = int(time.time()) + (3600 * (slash_count + 1))  # 1 hour, 2 hours, etc.
        cursor.execute('''
            INSERT INTO validator_jail (validator, jailed_until, slash_count, total_slashed)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(validator) DO UPDATE SET
                jailed_until = excluded.jailed_until,
                slash_count = slash_count + 1,
                total_slashed = total_slashed + excluded.total_slashed
        ''', (validator, jail_until, slash_count + 1, int(slash_percent * 100)))
        
        conn.commit()
        conn.close()
        
        logger.warning(f"Validator {validator} slashed for equivocation at height {block_height} - {slash_percent*100}% stake penalty")
        
        return {
            "slashed": True,
            "validator": validator,
            "offense": "equivocation (double-vote)",
            "slash_percent": f"{slash_percent*100}%",
            "jailed_until": datetime.fromtimestamp(jail_until).isoformat(),
            "slash_count": slash_count + 1
        }
    
    def is_jailed(self, validator: str) -> Dict:
        """Check if validator is currently jailed"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('SELECT jailed_until, slash_count FROM validator_jail WHERE validator = ?', (validator,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {"jailed": False, "reason": "No record"}
        
        jailed_until, slash_count = row
        now = int(time.time())
        
        if now < jailed_until:
            return {
                "jailed": True,
                "released_in": jailed_until - now,
                "released_at": datetime.fromtimestamp(jailed_until).isoformat(),
                "slash_count": slash_count
            }
        return {"jailed": False, "reason": "Sentence served"}
    
    def get_slashing_stats(self) -> Dict:
        """Get overall slashing statistics"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM slashing_events')
        total_events = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT validator) FROM slashing_events')
        unique_validators = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(slash_amount) FROM slashing_events')
        total_slashed = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_slashing_events": total_events,
            "unique_validators_slashed": unique_validators,
            "total_stake_slashed": total_slashed,
            "slashing_enabled": True,
            "max_penalty": "50%"
        }

slashing = SlashingManager()
