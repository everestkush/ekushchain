import os
"""Fee estimation algorithm - Smart fee recommendations based on mempool"""
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time
import statistics
from collections import deque
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class FeeEstimator:
    """Smart fee estimation based on historical block data and mempool"""
    
    # Fee tiers (satoshis per byte)
    FEE_TIERS = {
        "economy": 1,      # Minimum fee
        "low": 5,          # Slow (1-2 hours)
        "medium": 10,      # Normal (30-60 minutes)
        "high": 20,        # Fast (10-30 minutes)
        "priority": 50,    # Next block
    }
    
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")):
        self.db_path = db_path
        self.mempool_fees = deque(maxlen=1000)  # Last 1000 tx fees
        self.block_fees = deque(maxlen=100)     # Last 100 blocks avg fees
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fee_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                block_height INTEGER,
                avg_fee INTEGER,
                min_fee INTEGER,
                max_fee INTEGER,
                tx_count INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_transaction_fee(self, fee: int, size: int) -> None:
        """Add transaction fee to mempool history"""
        fee_per_byte = fee // size if size > 0 else fee
        self.mempool_fees.append(fee_per_byte)
        logger.debug(f"Added fee {fee_per_byte} sat/byte to mempool")
    
    def record_block_fees(self, block_height: int, transactions: List[Dict]) -> None:
        """Record fee statistics for a mined block"""
        if not transactions:
            return
        
        fees = []
        for tx in transactions:
            fee = tx.get('fee', 0)
            size = tx.get('size', 250)  # Default tx size
            if fee > 0:
                fees.append(fee // size)
        
        if fees:
            avg_fee = int(statistics.mean(fees))
            min_fee = min(fees)
            max_fee = max(fees)
            
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO fee_history (timestamp, block_height, avg_fee, min_fee, max_fee, tx_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (int(time.time()), block_height, avg_fee, min_fee, max_fee, len(fees)))
            conn.commit()
            conn.close()
            
            self.block_fees.append(avg_fee)
            logger.info(f"Block {block_height} avg fee: {avg_fee} sat/byte")
    
    def estimate_fee(self, target_blocks: int = 1) -> Dict:
        """Estimate fee for target confirmation blocks"""
        if target_blocks == 1:
            # Next block: use 95th percentile of mempool
            if self.mempool_fees:
                sorted_fees = sorted(self.mempool_fees)
                percentile_95 = sorted_fees[int(len(sorted_fees) * 0.95)]
                return {
                    "fee_per_byte": max(percentile_95, self.FEE_TIERS["priority"]),
                    "target_blocks": target_blocks,
                    "estimated_time": "~10 minutes"
                }
            return {"fee_per_byte": self.FEE_TIERS["priority"], "target_blocks": target_blocks}
        
        elif target_blocks <= 3:
            # Fast: use 75th percentile
            if self.mempool_fees:
                sorted_fees = sorted(self.mempool_fees)
                percentile_75 = sorted_fees[int(len(sorted_fees) * 0.75)]
                return {
                    "fee_per_byte": max(percentile_75, self.FEE_TIERS["high"]),
                    "target_blocks": target_blocks,
                    "estimated_time": "~30 minutes"
                }
            return {"fee_per_byte": self.FEE_TIERS["high"], "target_blocks": target_blocks}
        
        elif target_blocks <= 6:
            # Medium: use 50th percentile
            if self.mempool_fees:
                median = statistics.median(self.mempool_fees)
                return {
                    "fee_per_byte": max(int(median), self.FEE_TIERS["medium"]),
                    "target_blocks": target_blocks,
                    "estimated_time": "~1 hour"
                }
            return {"fee_per_byte": self.FEE_TIERS["medium"], "target_blocks": target_blocks}
        
        else:
            # Economy: use minimum
            return {
                "fee_per_byte": self.FEE_TIERS["economy"],
                "target_blocks": target_blocks,
                "estimated_time": "~2+ hours"
            }
    
    def get_fee_recommendations(self) -> Dict:
        """Get fee recommendations for all tiers"""
        return {
            "economy": {
                "fee_per_byte": self.FEE_TIERS["economy"],
                "target_blocks": 12,
                "description": "Minimum fee, slowest confirmation"
            },
            "low": {
                "fee_per_byte": self.FEE_TIERS["low"],
                "target_blocks": 6,
                "description": "Low priority, ~1-2 hours"
            },
            "medium": {
                "fee_per_byte": self.FEE_TIERS["medium"],
                "target_blocks": 3,
                "description": "Normal priority, ~30-60 minutes"
            },
            "high": {
                "fee_per_byte": self.FEE_TIERS["high"],
                "target_blocks": 1,
                "description": "High priority, ~10-30 minutes"
            },
            "priority": {
                "fee_per_byte": self.FEE_TIERS["priority"],
                "target_blocks": 1,
                "description": "Next block priority"
            }
        }
    
    def get_dynamic_recommendation(self) -> Dict:
        """Get dynamic fee based on current mempool conditions"""
        # Use dynamic if we have mempool data, otherwise fallback to defaults
        if self.mempool_fees:
            sorted_fees = sorted(self.mempool_fees)
            p50 = statistics.median(sorted_fees)
            p75 = sorted_fees[int(len(sorted_fees) * 0.75)]
            p95 = sorted_fees[int(len(sorted_fees) * 0.95)]
            
            return {
                "fastest": max(p95, self.FEE_TIERS["priority"]),
                "fast": max(p75, self.FEE_TIERS["high"]),
                "medium": max(int(p50), self.FEE_TIERS["medium"]),
                "slow": self.FEE_TIERS["low"],
                "mempool_size": len(self.mempool_fees),
                "is_dynamic": True
            }
        
        return {
            "fastest": self.FEE_TIERS["priority"],
            "fast": self.FEE_TIERS["high"],
            "medium": self.FEE_TIERS["medium"],
            "slow": self.FEE_TIERS["low"],
            "mempool_size": 0,
            "is_dynamic": False
        }
    
    def get_stats(self) -> Dict:
        """Get fee estimator statistics"""
        return {
            "enabled": True,
            "mempool_tx_count": len(self.mempool_fees),
            "historical_blocks": len(self.block_fees),
            "avg_fee_last_blocks": int(statistics.mean(self.block_fees)) if self.block_fees else 0,
            "fee_tiers": self.FEE_TIERS
        }

fee_estimator = FeeEstimator()
