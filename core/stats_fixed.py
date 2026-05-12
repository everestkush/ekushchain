from flask import jsonify
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import os

def get_stats():
    conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM blocks")
    chain_length = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_txs = cursor.fetchone()[0]
    
    cursor.execute("SELECT timestamp, idx FROM blocks ORDER BY idx DESC LIMIT 1")
    latest = cursor.fetchone()
    last_block_time = latest[0] if latest else None
    last_block_height = latest[1] if latest else 0
    
    cursor.execute("SELECT COUNT(*) FROM mempool")
    pending = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'chain_length': chain_length,
        'total_blocks': chain_length,
        'total_transactions': total_txs,
        'height': chain_length,
        'pending_transactions': pending,
        'last_block_time': last_block_time,
        'last_block_height': last_block_height,
        'chain_valid': True,
        'network': os.getenv('NETWORK_MODE', 'mainnet')
    }
