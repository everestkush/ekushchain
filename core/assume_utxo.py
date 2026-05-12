import os
"""AssumeUTXO - Fast sync bootstrapping with UTXO snapshots"""
import json
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import hashlib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AssumeUTXO:
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), snapshot_file="utxo_snapshot.dat"):
        self.db_path = db_path
        self.snapshot_file = Path(snapshot_file)
    
    def create_snapshot(self, block_height: int):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute("SELECT block_hash FROM blocks WHERE height=? AND is_active=1", (block_height,))
        block_hash = cursor.fetchone()[0]
        
        cursor.execute("SELECT outpoint, amount, script_pubkey, block_height FROM utxoset WHERE is_spent=0")
        utxos = []
        for row in cursor.fetchall():
            script = row[2].hex() if isinstance(row[2], bytes) else row[2]
            utxos.append({
                "outpoint": row[0],
                "amount": row[1],
                "script": script,
                "height": row[3]
            })
        
        snapshot = {
            "version": 1,
            "block_height": block_height,
            "block_hash": block_hash,
            "utxo_count": len(utxos),
            "utxos": utxos,
            "checksum": hashlib.sha256(json.dumps(utxos, sort_keys=True).encode()).hexdigest()
        }
        
        with open(self.snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2)
        
        logger.info(f"Snapshot created at height {block_height} with {len(utxos)} UTXOs")
        conn.close()
    
    def load_snapshot(self) -> bool:
        if not self.snapshot_file.exists():
            return False
        
        with open(self.snapshot_file) as f:
            snapshot = json.load(f)
        
        calc_hash = hashlib.sha256(json.dumps(snapshot["utxos"], sort_keys=True).encode()).hexdigest()
        if calc_hash != snapshot["checksum"]:
            raise ValueError("Snapshot checksum mismatch")
        
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM utxoset")
        
        for utxo in snapshot["utxos"]:
            script = bytes.fromhex(utxo["script"]) if isinstance(utxo["script"], str) else utxo["script"]
            cursor.execute("""
                INSERT INTO utxoset (outpoint, amount, script_pubkey, block_height, is_spent) 
                VALUES (?, ?, ?, ?, 0)
            """, (utxo["outpoint"], utxo["amount"], script, utxo["height"]))
        
        conn.commit()
        conn.close()
        logger.info(f"Loaded snapshot: {snapshot['utxo_count']} UTXOs at height {snapshot['block_height']}")
        return True
