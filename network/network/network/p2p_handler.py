"""P2P message handlers for block sync"""
import json
import sqlite3

DB_PATH = "/home/kushal/everestkush/ekush_chain.db"

def get_headers(from_height, max_count=2000):
    """Get block headers from height"""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute('''
        SELECT idx, hash, previous_hash, timestamp 
        FROM blocks WHERE idx > ? ORDER BY idx LIMIT ?
    ''', (from_height, max_count))
    headers = [{'height': r[0], 'hash': r[1], 'prev_hash': r[2], 'timestamp': r[3]} for r in rows]
    conn.close()
    return headers

def get_blocks(from_height, max_count=500):
    """Get block data from height"""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute('''
        SELECT idx, hash, previous_hash, validator, timestamp 
        FROM blocks WHERE idx > ? ORDER BY idx LIMIT ?
    ''', (from_height, max_count))
    blocks = [{'idx': r[0], 'hash': r[1], 'prev_hash': r[2], 'validator': r[3], 'timestamp': r[4]} for r in rows]
    conn.close()
    return blocks

def handle_message(peer, msg_type, payload):
    """Handle incoming P2P messages"""
    if msg_type == 'getheaders':
        from_height = payload.get('from', 0)
        headers = get_headers(from_height)
        return {'type': 'headers', 'data': headers}
    
    elif msg_type == 'getblocks':
        from_height = payload.get('from', 0)
        blocks = get_blocks(from_height)
        return {'type': 'blocks', 'data': blocks}
    
    elif msg_type == 'ping':
        return {'type': 'pong', 'data': {}}
    
    return None
