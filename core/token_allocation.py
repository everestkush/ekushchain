import os
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time
import hashlib

class TokenAllocation:
    
    ALLOCATIONS = {

        'public': ('Public Allocation', 300_000_000, 30, 1, 0, 0),

        'validator': ('Validator Rewards', 300_000_000, 30, 5, 0, 0),

        'development': ('Development Fund', 150_000_000, 15, 5, 563, 0),

        'ecosystem': ('Ecosystem Fund', 150_000_000, 15, 5, 928, 0),

        'crisis': ('Crisis Reserve', 100_000_000, 10, 15, 2761, 0)

    }
    
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS allocation_wallets (
                id TEXT PRIMARY KEY,
                name TEXT,
                address TEXT,
                amount INTEGER,
                percentage INTEGER,
                multisig_required INTEGER,
                vesting_days INTEGER,
                cliff_days INTEGER,
                released_amount INTEGER DEFAULT 0,
                created_at INTEGER,
                status TEXT DEFAULT 'active'
            )
        ''')
        conn.commit()
        conn.close()
    
    def generate_address(self, key):
        from core.segwit import SegWitAddress
        seed = f"everestkush_allocation_{key}_2026"
        pubkey_hash = hashlib.sha256(seed.encode()).digest()[:20]
        return SegWitAddress.p2wpkh_from_pubkey(pubkey_hash)
    
    def create_wallets(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        c = conn.cursor()
        
        for key, (name, amount, percent, multisig, vesting, cliff) in self.ALLOCATIONS.items():
            address = self.generate_address(key)
            c.execute('''
                INSERT OR REPLACE INTO allocation_wallets 
                (id, name, address, amount, percentage, multisig_required, 
                 vesting_days, cliff_days, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (key, name, address, amount, percent, multisig, vesting, cliff, int(time.time()), 'active'))
        
        conn.commit()
        conn.close()
        return True
    
    def get_info(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        c = conn.cursor()
        c.execute('SELECT id, name, address, amount, percentage, multisig_required, vesting_days, cliff_days, released_amount, status FROM allocation_wallets')
        rows = c.fetchall()
        conn.close()
        
        wallets = []
        for row in rows:
            wallets.append({
                'id': row[0],
                'name': row[1],
                'address': row[2],
                'amount': row[3],
                'percentage': row[4],
                'multisig_required': row[5],
                'vesting_days': row[6],
                'cliff_days': row[7],
                'released': row[8],
                'status': row[9]
            })
        
        return {
            'total_supply': 1_000_000_000,
            'allocated': sum(w['amount'] for w in wallets),
            'wallets': wallets
        }

token_allocation = TokenAllocation()
