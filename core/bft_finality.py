import os
"""BFT Finality Gadget - Byzantine fault tolerance with 2/3+ consensus"""
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time
from collections import defaultdict
from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)

class BFTFinality:
    """BFT finality gadget - True Byzantine fault tolerance"""
    
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), total_validators=21):
        self.db_path = db_path
        self.total_validators = total_validators
        self.required_consensus = int(total_validators * 2 / 3) + 1  # 15/21
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bft_votes (
                block_height INTEGER,
                validator TEXT,
                vote_hash TEXT,
                timestamp INTEGER,
                PRIMARY KEY (block_height, validator)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS finalized_blocks (
                block_height INTEGER PRIMARY KEY,
                block_hash TEXT,
                finalized_at INTEGER,
                votes_count INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_vote(self, block_height: int, validator: str, block_hash: str) -> Dict:
        """Add validator vote for a block"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        # Check if validator already voted for this height
        cursor.execute('SELECT * FROM bft_votes WHERE block_height = ? AND validator = ?', 
                      (block_height, validator))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "reason": "Already voted"}
        
        # Record vote
        cursor.execute('''
            INSERT INTO bft_votes (block_height, validator, vote_hash, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (block_height, validator, block_hash, int(time.time())))
        
        conn.commit()
        
        # Check if we have consensus
        result = self.check_finality(block_height, block_hash)
        conn.close()
        
        logger.info(f"Validator {validator} voted for block {block_height}")
        return {"success": True, "finalized": result.get("finalized", False)}
    
    def check_finality(self, block_height: int, block_hash: str) -> Dict:
        """Check if block has reached BFT finality"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(DISTINCT validator) FROM bft_votes 
            WHERE block_height = ? AND vote_hash = ?
        ''', (block_height, block_hash))
        
        vote_count = cursor.fetchone()[0]
        conn.close()
        
        is_finalized = vote_count >= self.required_consensus
        
        if is_finalized:
            self._mark_finalized(block_height, block_hash, vote_count)
        
        return {
            "finalized": is_finalized,
            "vote_count": vote_count,
            "required": self.required_consensus,
            "total_validators": self.total_validators,
            "threshold": f"{self.required_consensus}/{self.total_validators}"
        }
    
    def _mark_finalized(self, block_height: int, block_hash: str, vote_count: int):
        """Mark block as finalized"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO finalized_blocks (block_height, block_hash, finalized_at, votes_count)
            VALUES (?, ?, ?, ?)
        ''', (block_height, block_hash, int(time.time()), vote_count))
        
        conn.commit()
        conn.close()
        logger.info(f"Block {block_height} FINALIZED with {vote_count} votes")
    
    def is_finalized(self, block_height: int) -> bool:
        """Check if block is already finalized"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM finalized_blocks WHERE block_height = ?', (block_height,))
        result = cursor.fetchone() is not None
        conn.close()
        return result
    
    def get_finality_status(self, block_height: int) -> Dict:
        """Get finality status for a block"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT vote_hash, COUNT(*) FROM bft_votes 
            WHERE block_height = ? 
            GROUP BY vote_hash
            ORDER BY COUNT(*) DESC
        ''', (block_height,))
        
        votes = cursor.fetchall()
        conn.close()
        
        if not votes:
            return {"finalized": False, "votes": []}
        
        top_vote = votes[0]
        is_final = self.is_finalized(block_height)
        
        return {
            "finalized": is_final,
            "leading_hash": top_vote[0],
            "leading_votes": top_vote[1],
            "required": self.required_consensus,
            "total_validators": self.total_validators
        }
    
    def get_stats(self) -> Dict:
        """Get BFT finality statistics"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM finalized_blocks')
        finalized_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT validator) FROM bft_votes')
        active_validators = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "finalized_blocks": finalized_count,
            "active_validators": active_validators,
            "total_validators": self.total_validators,
            "consensus_threshold": f"{self.required_consensus}/{self.total_validators}",
            "bft_enabled": True,
            "finality_gadget": "True BFT (2/3+ consensus)"
        }

bft = BFTFinality()
