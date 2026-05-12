import os
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import secrets
import time
from typing import List, Dict

class AirdropManager:
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS airdrop_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE,
                amount INTEGER,
                claimed INTEGER DEFAULT 0,
                claimed_at INTEGER,
                referral_code TEXT,
                referred_by TEXT,
                created_at INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    
    def generate_wallets(self, count: int, amount_per_wallet: int) -> List[Dict]:
        from core.segwit import SegWitAddress
        import hashlib
        
        wallets = []
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        for i in range(count):
            seed = f"airdrop_wallet_{i}_{int(time.time())}"
            pubkey_hash = hashlib.sha256(seed.encode()).digest()[:20]
            address = SegWitAddress.p2wpkh_from_pubkey(pubkey_hash)
            referral_code = secrets.token_hex(4).upper()
            
            cursor.execute('''
                INSERT OR IGNORE INTO airdrop_recipients 
                (address, amount, referral_code, created_at)
                VALUES (?, ?, ?, ?)
            ''', (address, amount_per_wallet, referral_code, int(time.time())))
            
            wallets.append({
                'address': address,
                'amount': amount_per_wallet,
                'referral_code': referral_code
            })
        
        conn.commit()
        conn.close()
        return wallets
    
    def claim_airdrop(self, address: str) -> Dict:
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT amount, claimed FROM airdrop_recipients 
            WHERE address = ? AND claimed = 0
        ''', (address,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {"error": "No airdrop found for this address"}
        
        amount = row[0]
        
        cursor.execute('''
            UPDATE airdrop_recipients 
            SET claimed = 1, claimed_at = ? 
            WHERE address = ?
        ''', (int(time.time()), address))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "address": address, "amount": amount}
    
    def get_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM airdrop_recipients')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM airdrop_recipients WHERE claimed = 1')
        claimed_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(amount) FROM airdrop_recipients')
        total_amount = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(amount) FROM airdrop_recipients WHERE claimed = 1')
        claimed_amount = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_recipients': total,
            'claimed_recipients': claimed_count,
            'unclaimed_recipients': total - claimed_count,
            'total_amount': total_amount,
            'claimed_amount': claimed_amount,
            'unclaimed_amount': total_amount - claimed_amount
        }

airdrop = AirdropManager()
