"""
EKUSH Block Sync Protocol
Handles block download from peers for new nodes joining the network
"""
import json
import socket
import sqlite3
import time
import threading

DB_PATH = "/home/kushal/everestkush/ekush_chain.db"
SEED_NODES = [
    "103.74.15.88:8333"
]

def get_local_height():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        h = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
        conn.close()
        return h
    except:
        return 0

def get_blocks_from_peer(peer_ip, peer_port, start_height, max_blocks=50):
    """Request blocks from a peer starting at start_height."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((peer_ip, int(peer_port)))
        
        # Send getblocks request
        msg = json.dumps({
            "type": "getblocks",
            "payload": {
                "start_height": start_height,
                "max_blocks": max_blocks
            }
        }).encode()
        s.sendall(msg)
        
        # Receive response
        data = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
            try:
                response = json.loads(data.decode())
                s.close()
                return response.get("blocks", [])
            except json.JSONDecodeError:
                continue
        s.close()
        return []
    except Exception as e:
        print(f"⚠️ Sync error from {peer_ip}:{peer_port} — {e}")
        return []

def save_synced_block(block_data):
    """Save a block received from a peer."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        
        # Check if block already exists
        exists = conn.execute(
            "SELECT idx FROM blocks WHERE idx = ?", 
            (block_data["idx"],)
        ).fetchone()
        
        if exists:
            conn.close()
            return False
        
        conn.execute("""
            INSERT INTO blocks 
            (idx, hash, previous_hash, validator, timestamp, nonce, merkle_root, transactions_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            block_data["idx"],
            block_data["hash"],
            block_data["previous_hash"],
            block_data.get("validator", ""),
            block_data.get("timestamp", int(time.time())),
            block_data.get("nonce", 0),
            block_data.get("merkle_root", ""),
            block_data.get("transactions_count", 0)
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"⚠️ Save block error: {e}")
        return False

def sync_from_peer(peer_ip, peer_port=8333):
    """Full sync from a single peer."""
    local_height = get_local_height()
    print(f"🔄 Syncing from {peer_ip}:{peer_port} — local height: {local_height}")
    
    synced = 0
    while True:
        blocks = get_blocks_from_peer(peer_ip, peer_port, local_height, max_blocks=50)
        if not blocks:
            break
        
        for block in blocks:
            if save_synced_block(block):
                synced += 1
                local_height += 1
        
        print(f"🔄 Synced {synced} blocks — now at height {local_height}")
        
        if len(blocks) < 50:
            break  # No more blocks
    
    print(f"✅ Sync complete — {synced} new blocks — height: {local_height}")
    return synced

def auto_sync():
    """Background sync thread — runs on startup."""
    time.sleep(5)  # Wait for node to start
    
    for seed in SEED_NODES:
        try:
            ip, port = seed.split(":")
            synced = sync_from_peer(ip, int(port))
            if synced > 0:
                print(f"✅ Auto-sync: got {synced} blocks from {seed}")
                return
        except Exception as e:
            print(f"⚠️ Auto-sync failed from {seed}: {e}")
    
    print("⚠️ Auto-sync: no blocks received from seed nodes")

def start_auto_sync():
    """Start background sync thread."""
    t = threading.Thread(target=auto_sync, daemon=True)
    t.start()
    return t
