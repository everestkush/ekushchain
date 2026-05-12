import os
"""Deterministic wallet generation from seed phrases (BIP39/BIP32)"""
import hashlib
import hmac
import secrets
from typing import Tuple, Dict
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)

class DeterministicWallet:
    """BIP39/BIP32 deterministic wallet"""
    
    # BIP39 wordlist (simplified - in production use full 2048 words)
    WORDLIST = [
        "abandon", "ability", "able", "about", "above", "absent", "absorb", 
        "abstract", "absurd", "abuse", "access", "accident", "account", "accuse"
    ]
    
    @staticmethod
    def generate_mnemonic(strength: int = 128) -> str:
        """Generate BIP39 mnemonic seed phrase"""
        entropy = secrets.token_bytes(strength // 8)
        entropy_bits = bin(int.from_bytes(entropy, 'big'))[2:].zfill(strength)
        
        # Calculate checksum
        checksum = bin(int(hashlib.sha256(entropy).hexdigest(), 16))[2:].zfill(256)[:strength // 32]
        full_bits = entropy_bits + checksum
        
        # Convert to words
        words = []
        for i in range(0, len(full_bits), 11):
            index = int(full_bits[i:i+11], 2)
            words.append(DeterministicWallet.WORDLIST[index % len(DeterministicWallet.WORDLIST)])
        
        return ' '.join(words)
    
    @staticmethod
    def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
        """Convert mnemonic to seed using PBKDF2"""
        mnemonic_bytes = mnemonic.encode('utf-8')
        salt = ("mnemonic" + passphrase).encode('utf-8')
        return hashlib.pbkdf2_hmac('sha512', mnemonic_bytes, salt, 2048, 64)
    
    @staticmethod
    def derive_address(seed: bytes, index: int) -> str:
        """Derive deterministic address from seed"""
        # Simplified deterministic derivation
        derivation = hashlib.sha256(seed + index.to_bytes(4, 'big')).digest()
        pubkey_hash = derivation[:20]
        
        # Convert to bech32 SegWit address
        from core.segwit import SegWitAddress
        return SegWitAddress.p2wpkh_from_pubkey(pubkey_hash)
    
    @staticmethod
    def create_wallet_from_mnemonic(mnemonic: str, wallet_name: str) -> Dict:
        """Create deterministic wallet from mnemonic"""
        seed = DeterministicWallet.mnemonic_to_seed(mnemonic)
        
        # Store wallet in database
        conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deterministic_wallets (
                wallet_name TEXT PRIMARY KEY,
                mnemonic TEXT,
                seed_hash TEXT,
                created_at INTEGER
            )
        ''')
        
        seed_hash = hashlib.sha256(seed).hexdigest()
        cursor.execute('''
            INSERT OR REPLACE INTO deterministic_wallets (wallet_name, mnemonic, seed_hash, created_at)
            VALUES (?, ?, ?, ?)
        ''', (wallet_name, mnemonic, seed_hash, int(__import__('time').time())))
        
        conn.commit()
        conn.close()
        
        # Derive first address
        address = DeterministicWallet.derive_address(seed, 0)
        
        return {
            "wallet_name": wallet_name,
            "mnemonic": mnemonic,
            "address": address,
            "type": "BIP39/BIP32 Deterministic"
        }
    
    @staticmethod
    def get_wallet_address(wallet_name: str, index: int = 0) -> Dict:
        """Get deterministic address for wallet"""
        conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('SELECT mnemonic FROM deterministic_wallets WHERE wallet_name = ?', (wallet_name,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {"error": f"Wallet '{wallet_name}' not found"}
        
        seed = DeterministicWallet.mnemonic_to_seed(row[0])
        address = DeterministicWallet.derive_address(seed, index)
        
        return {
            "wallet_name": wallet_name,
            "address": address,
            "index": index,
            "type": "BIP39/BIP32 Deterministic"
        }
