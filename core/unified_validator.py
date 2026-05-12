import os
"""
Unified Validator Manager - JSON + Database sync
"""
import json
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time
from typing import Dict, List, Any

DB_PATH = "/home/kushal/everestkush/ekush_chain.db"
JSON_PATH = "/home/kushal/everestkush/validators.json"
MIN_BOND = 8888  # EKUSH (8888 * 1,000,000 base units)

class UnifiedValidatorManager:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validators (
                address TEXT PRIMARY KEY,
                name TEXT,
                bond INTEGER,
                node_url TEXT,
                blocks_produced INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                registered_at INTEGER,
                last_active INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    
    def sync_from_json(self):
        """Sync validators.json to database"""
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)
        
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        for address, info in data['candidates'].items():
            if info.get('active'):
                cursor.execute('''
                    INSERT OR REPLACE INTO validators 
                    (address, name, bond, node_url, blocks_produced, active, registered_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    address,
                    info.get('name', 'Validator'),
                    int(info.get('stake', 0) / 1000000) if info.get('stake') else MIN_BOND,
                    info.get('node_url', ''),
                    info.get('blocks_produced', 0),
                    1,
                    int(info.get('registered_at', time.time()))
                ))
        
        conn.commit()
        conn.close()
        print(f"[OK] Synced {len(data['active'])} validators to DB")
    
    def register_validator(self, address: str, name: str, node_url: str, bond: int) -> Dict:
        """Register new validator with 8888 EKUSH bond"""
        if bond < MIN_BOND:
            return {'error': f'Need minimum {MIN_BOND} EKUSH bond', 'success': False}
        
        # Check balance from main chain
        balance = self.get_balance(address)
        if balance < bond * 1000000:
            return {'error': f'Insufficient balance. Need {bond} EKUSH', 'success': False}
        
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        # Lock the bond
        self.lock_bond(address, bond)
        
        # Register
        cursor.execute('''
            INSERT INTO validators (address, name, bond, node_url, active, registered_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (address, name, bond, node_url, 1, int(time.time()), int(time.time())))
        
        # Also add to JSON
        self.add_to_json(address, name, node_url, bond)
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Validator {name} registered with {bond} EKUSH bond'}
    
    def get_balance(self, address: str) -> int:
        """Get balance in base units"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM wallets WHERE address = ?", (address,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0
    
    def lock_bond(self, address: str, amount: int):
        """Lock bond amount from being spent"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE wallets SET locked = locked + ? WHERE address = ?
        ''', (amount * 1000000, address))
        conn.commit()
        conn.close()
    
    def add_to_json(self, address: str, name: str, node_url: str, bond: int):
        """Add validator to validators.json"""
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)
        
        data['candidates'][address] = {
            'address': address,
            'stake': bond * 1000000,
            'node_url': node_url,
            'name': name,
            'votes': 0,
            'registered_at': time.time(),
            'blocks_produced': 0,
            'active': True
        }
        
        if address not in data['active']:
            data['active'].append(address)
        
        with open(JSON_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    
    def list_validators(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT address, name, bond, node_url, blocks_produced, active 
            FROM validators WHERE active = 1
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'address': r[0],
            'name': r[1],
            'bond': r[2],
            'node_url': r[3],
            'blocks_produced': r[4],
            'active': bool(r[5])
        } for r in rows]

print("[OK] Unified Validator Manager ready")
print(f"   Minimum bond: {MIN_BOND} EKUSH")
