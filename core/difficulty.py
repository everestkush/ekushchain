import os
"""APR-based reward system for EKUSH"""
import sqlite3

class DifficultyAdjustment:
    BLOCKS_PER_YEAR = 10_512_000
    YEAR_1_BLOCKS = BLOCKS_PER_YEAR
    TARGET_APR = 0.06  # 6% APR after year 1
    
    def __init__(self):
        self.target_block_time = 3
    
    def get_block_reward(self, block_height):
        """Get block reward based on APR"""
        # Year 1: Fixed 5 EKUSH
        if block_height < self.YEAR_1_BLOCKS:
            return 5
        
        # Year 2+: Calculate based on staked amount
        total_staked = self._get_total_staked()
        yearly_rewards = total_staked * self.TARGET_APR
        reward_per_block = yearly_rewards / self.BLOCKS_PER_YEAR
        return max(1, reward_per_block)
    
    def _get_total_staked(self):
        """Get total EKUSH staked by active validators"""
        try:
            conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
            row = conn.execute("SELECT COALESCE(SUM(bonded_amount), 0) FROM validators WHERE status='active'").fetchone()
            conn.close()
            return row[0] / 1_000_000 if row and row[0] else 0
        except:
            return 0
    
    def calculate_new_difficulty(self, chain, current_difficulty):
        return current_difficulty
    
    def get_supply_info(self, chain):
        block_height = len(chain.chain)
        return {
            "initial_reward": 5,
            "current_reward": self.get_block_reward(block_height),
            "target_apr": self.TARGET_APR,
            "total_staked": self._get_total_staked()
        }
