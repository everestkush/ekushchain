"""Validator reward halving mechanism - 28 initial reward, 28 years"""
import sqlite3

class HalvingManager:
    
    INITIAL_REWARD = 28
    HALVING_INTERVAL = 10_512_000
    MAX_HALVINGS = 28
    MAX_TOTAL_REWARDS = 200_000_000
    
    @staticmethod
    def get_current_reward(block_height: int) -> float:
        halvings = block_height // HalvingManager.HALVING_INTERVAL
        if halvings >= HalvingManager.MAX_HALVINGS:
            halvings = HalvingManager.MAX_HALVINGS
        reward = HalvingManager.INITIAL_REWARD / (2 ** halvings)
        return reward
    
    @staticmethod
    def get_next_halving_block(current_height: int) -> int:
        return ((current_height // HalvingManager.HALVING_INTERVAL) + 1) * HalvingManager.HALVING_INTERVAL
    
    @staticmethod
    def get_blocks_to_halving(current_height: int) -> int:
        next_halving = HalvingManager.get_next_halving_block(current_height)
        return next_halving - current_height
    
    @staticmethod
    def get_info(current_height: int) -> dict:
        current_reward = HalvingManager.get_current_reward(current_height)
        next_halving = HalvingManager.get_next_halving_block(current_height)
        blocks_left = HalvingManager.get_blocks_to_halving(current_height)
        halving_count = current_height // HalvingManager.HALVING_INTERVAL
        years_to_next = blocks_left * 3 / (365 * 24 * 3600)
        
        return {
            'current_reward': current_reward,
            'next_halving_block': next_halving,
            'blocks_to_halving': blocks_left,
            'years_to_next_halving': round(years_to_next, 2),
            'halving_count': halving_count,
            'initial_reward': HalvingManager.INITIAL_REWARD,
            'halving_interval': HalvingManager.HALVING_INTERVAL,
            'max_rewards_pool': HalvingManager.MAX_TOTAL_REWARDS,
            'message': '28 EKUSH initial reward, halving every ~1 year. Total validator pool: 200M EKUSH.'
        }

halving = HalvingManager()
