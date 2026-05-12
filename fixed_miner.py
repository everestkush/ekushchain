#!/usr/bin/env python3
import os
import sys, time, sqlite3, threading
sys.path.insert(0, '/home/kushal/everestkush')

from core.block import EKUSHChain
from network.p2p_server import start_p2p

print("Starting P2P server...")
start_p2p()
print("[P2P] Server running on port 8333")

print("Loading blockchain ONCE...")
bc = EKUSHChain()
print(f"Loaded {len(bc.chain)} blocks")

# Get validator
conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=60)
row = conn.execute("SELECT address FROM validators WHERE status='active' LIMIT 1").fetchone()
conn.close()
if not row:
    print("[MINER] No active validator found. Waiting...")
    while True:
        time.sleep(10)
        conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=60)
        row = conn.execute("SELECT address FROM validators WHERE status='active' LIMIT 1").fetchone()
        conn.close()
        if row:
            break
        print("[MINER] Still waiting for validator registration...")
validator = row[0]
print(f"Mining with validator: {validator[:30]}...")

print("[MINER] Started - mining every 3 seconds")

while True:
    try:
        block = bc.add_block(validator)
        if block:
            from network.p2p_gossip import p2p_gossip
            p2p_gossip.broadcast_block(block.hash)
        if block:
            print(f"[MINER] Block #{block.index} mined")
        time.sleep(8)
    except Exception as e:
        print(f"Miner error: {e}")
        time.sleep(8)
