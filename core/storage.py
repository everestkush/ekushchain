import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import json
import os
from core.transaction import EKUSHTransaction

DB_PATH = "/home/kushal/everestkush/ekush_chain.db"

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            idx         INTEGER PRIMARY KEY,
            hash        TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            validator   TEXT NOT NULL,
            timestamp   REAL NOT NULL,
            nonce       INTEGER DEFAULT 0,
            merkle_root TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            tx_hash     TEXT PRIMARY KEY,
            block_idx   INTEGER,
            sender      TEXT NOT NULL,
            recipient   TEXT NOT NULL,
            amount      REAL NOT NULL,
            fee         REAL NOT NULL,
            timestamp   REAL NOT NULL,
            signature   TEXT,
            FOREIGN KEY (block_idx) REFERENCES blocks(idx)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS pending_transactions (
            tx_hash     TEXT PRIMARY KEY,
            sender      TEXT NOT NULL,
            recipient   TEXT NOT NULL,
            amount      REAL NOT NULL,
            fee         REAL NOT NULL,
            timestamp   REAL NOT NULL,
            signature   TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print(f"EverestKush database initialized at {DB_PATH}")



from core.storage_backend import storage

def save_block(block):
    if storage:
        storage.save_block(block)
    else:
        _save_block_sqlite(block)

def _save_block_sqlite(block):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO blocks (idx, hash, previous_hash, validator, timestamp, nonce, merkle_root) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (block.index, block.hash, block.previous_hash, block.validator, block.timestamp, block.nonce, block.merkle_root))
    for tx in block.transactions:
        c.execute('INSERT OR REPLACE INTO transactions (tx_hash, block_idx, sender, recipient, amount, fee, timestamp, signature) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                  (tx.calculate_hash(), block.index, tx.sender, tx.recipient, tx.amount, tx.fee, tx.timestamp, tx.signature.hex() if tx.signature else None))
    conn.commit()
    conn.close()

    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()

    c.execute('''
        INSERT OR REPLACE INTO blocks
        (idx, hash, previous_hash, validator, timestamp, nonce, merkle_root)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        block.index,
        block.hash,
        block.previous_hash,
        block.validator,
        block.timestamp,
        block.nonce,
        block.calculate_merkle_root()
    ))

    for tx in block.transactions:
        c.execute('''
            INSERT OR REPLACE INTO transactions
            (tx_hash, block_idx, sender, recipient, amount, fee, timestamp, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tx.calculate_hash(),
            block.index,
            tx.sender,
            tx.recipient,
            tx.amount,
            tx.fee,
            tx.timestamp,
            tx.signature.hex() if tx.signature else None
        ))

    conn.commit()
    conn.close()


def load_chain():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()

    c.execute('SELECT idx FROM blocks ORDER BY idx')
    block_rows = c.fetchall()

    if not block_rows:
        conn.close()
        return []

    blocks_data = []
    for (idx,) in block_rows:
        c.execute('SELECT * FROM blocks WHERE idx = ?', (idx,))
        b = c.fetchone()

        c.execute('''
            SELECT sender, recipient, amount, fee, timestamp, signature
            FROM transactions WHERE block_idx = ? ORDER BY timestamp
        ''', (idx,))
        tx_rows = c.fetchall()

        transactions = []
        for tx_row in tx_rows:
            tx = EKUSHTransaction(
                sender=tx_row[0],
                recipient=tx_row[1],
                amount=tx_row[2],
                fee=tx_row[3],
                timestamp=tx_row[4]
            )
            if tx_row[5]:
                tx.signature = bytes.fromhex(tx_row[5])
            transactions.append(tx)

        blocks_data.append({
            "index": b[0],
            "hash": b[1],
            "previous_hash": b[2],
            "validator": b[3],
            "timestamp": b[4],
            "nonce": b[5],
            "transactions": transactions
        })

    conn.close()
    return blocks_data


def chain_exists():
    if not os.path.exists(DB_PATH):
        return False
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM blocks')
    count = c.fetchone()[0]
    conn.close()
    return count > 0


def save_pending(tx):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO pending_transactions
        (tx_hash, sender, recipient, amount, fee, timestamp, signature)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        tx.calculate_hash(),
        tx.sender,
        tx.recipient,
        tx.amount,
        tx.fee,
        tx.timestamp,
        tx.signature.hex() if tx.signature else None
    ))
    conn.commit()
    conn.close()


def load_pending():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()
    c.execute('SELECT sender, recipient, amount, fee, timestamp, signature FROM pending_transactions')
    rows = c.fetchall()
    conn.close()

    transactions = []
    for row in rows:
        tx = EKUSHTransaction(
            sender=row[0],
            recipient=row[1],
            amount=row[2],
            fee=row[3],
            timestamp=row[4]
        )
        if row[5]:
            tx.signature = bytes.fromhex(row[5])
        transactions.append(tx)
    return transactions


def clear_pending():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()
    c.execute('DELETE FROM pending_transactions')
    conn.commit()
    conn.close()


def get_chain_stats():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM blocks')
    block_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM transactions')
    tx_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM pending_transactions')
    pending_count = c.fetchone()[0]
    conn.close()
    return {
        "blocks": block_count,
        "transactions": tx_count,
        "pending": pending_count
    }

# Allow DB path override via environment
import os
DB_PATH = os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db')
