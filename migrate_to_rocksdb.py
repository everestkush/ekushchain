#!/usr/bin/env python3
"""
Migrate EverestKush from SQLite to RocksDB
"""
import sqlite3
import json
import os
import time
from rocksdict import Rdict

# Paths
SQLITE_PATH = "/home/kushal/everestkush/ekush_chain.db"
ROCKSDB_PATH = "/home/kushal/everestkush/rocksdb_data"

# Create RocksDB instances for different data types
blocks_db = Rdict(f"{ROCKSDB_PATH}/blocks")
txs_db = Rdict(f"{ROCKSDB_PATH}/transactions")
utxos_db = Rdict(f"{ROCKSDB_PATH}/utxos")
chainstate_db = Rdict(f"{ROCKSDB_PATH}/chainstate")
metadata_db = Rdict(f"{ROCKSDB_PATH}/metadata")

print("[START] Starting SQLite to RocksDB Migration")
print("=" * 50)

# Connect to SQLite
conn = sqlite3.connect(SQLITE_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Migrate blocks
print("\n[BLOCK] Migrating blocks...")
cur.execute("SELECT * FROM blocks ORDER BY idx")
blocks = cur.fetchall()
for block in blocks:
    key = f"block:{block['idx']}".encode()
    value = json.dumps(dict(block)).encode()
    blocks_db[key] = value
print(f"   [OK] Migrated {len(blocks)} blocks")

# 2. Migrate transactions
print("\n[BLOCK] Migrating transactions...")
cur.execute("SELECT * FROM transactions")
txs = cur.fetchall()
for tx in txs:
    key = f"tx:{tx['tx_hash']}".encode()
    value = json.dumps(dict(tx)).encode()
    txs_db[key] = value
print(f"   [OK] Migrated {len(txs)} transactions")

# 3. Migrate UTXOs
print("\n[BLOCK] Migrating UTXOs...")
cur.execute("SELECT * FROM utxos WHERE is_spent = 0")
utxos = cur.fetchall()
for utxo in utxos:
    key = f"utxo:{utxo['outpoint']}".encode()
    value = json.dumps(dict(utxo)).encode()
    utxos_db[key] = value
print(f"   [OK] Migrated {len(utxos)} UTXOs")

# 4. Migrate chainstate (best block)
print("\n[BLOCK] Migrating chainstate...")
cur.execute("SELECT MAX(idx) as height FROM blocks")
best_block = cur.fetchone()
chainstate_db[b'best_height'] = str(best_block['height']).encode()
chainstate_db[b'best_hash'] = blocks[-1]['hash'].encode()
print(f"   [OK] Best block height: {best_block['height']}")

# 5. Store metadata
print("\n[BLOCK] Storing metadata...")
metadata_db[b'migration_time'] = str(int(time.time())).encode()
metadata_db[b'source'] = b'sqlite'
metadata_db[b'total_blocks'] = str(len(blocks)).encode()
print(f"   [OK] Metadata stored")

conn.close()

# Close all RocksDB instances
blocks_db.close()
txs_db.close()
utxos_db.close()
chainstate_db.close()
metadata_db.close()

print("\n" + "=" * 50)
print(f"[OK] Migration complete!")
print(f"   RocksDB data stored at: {ROCKSDB_PATH}")
print(f"   Total size: {os.path.getsize(ROCKSDB_PATH)} bytes")
