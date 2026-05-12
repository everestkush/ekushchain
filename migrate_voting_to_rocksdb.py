#!/usr/bin/env python3
import sqlite3
import json
import os
from rocksdict import Rdict

SQLITE_PATH = "/home/kushal/everestkush/ekush_chain.db"
ROCKSDB_PATH = "/home/kushal/everestkush/rocksdb_data"

# Voting tables and their RocksDB column family (subdirectory)
TABLES = {
    "voters": "voters",
    "votes": "votes",
    "governance_proposals": "gov_proposals",
    "governance_votes": "gov_votes",
    "elections": "elections",
    "election_votes": "election_votes",
    "election_results": "election_results",
    "proposals": "proposals",
    "proposal_options": "proposal_options",
}

# Create directories
for cf in TABLES.values():
    os.makedirs(f"{ROCKSDB_PATH}/{cf}", exist_ok=True)

conn = sqlite3.connect(SQLITE_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

for sqlite_table, rocksdb_cf in TABLES.items():
    try:
        cur.execute(f"SELECT * FROM {sqlite_table}")
        rows = cur.fetchall()
        if not rows:
            print(f"Skipping empty table: {sqlite_table}")
            continue
        db = Rdict(f"{ROCKSDB_PATH}/{rocksdb_cf}")
        count = 0
        for row in rows:
            # Use first column as key (assumed unique)
            key = str(row[0]).encode()
            db[key] = json.dumps(dict(row)).encode()
            count += 1
        db.close()
        print(f"Migrated {count} rows from {sqlite_table}")
    except sqlite3.OperationalError as e:
        print(f"Table {sqlite_table} not found: {e}")

conn.close()
print("Voting data migration completed.")
