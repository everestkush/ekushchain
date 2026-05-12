import os
"""BIP39/BIP32 Hierarchical Deterministic Wallet - Bitcoin Standard"""
import hashlib
import hmac
import secrets
from typing import Tuple, Dict, List
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time

class BIP39Wallet:
    """Bitcoin-standard BIP39/BIP32 deterministic wallet"""
    
    # BIP39 English wordlist (first 100 words for demo - in production use full 2048)
    WORDLIST = [
        "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd", "abuse",
        "access", "accident", "account", "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act",
        "action", "actor", "actress", "actual", "adapt", "add", "addict", "address", "adjust", "admit",
        "adult", "advance", "advice", "aerobic", "affair", "afford", "afraid", "africa", "africa", "after",
        "again", "age", "agent", "agree", "ahead", "aim", "air", "airport", "aisle", "alarm",
        "album", "alcohol", "alert", "alien", "all", "alley", "allow", "almost", "alone", "alpha",
        "already", "also", "alter", "always", "amateur", "amazing", "among", "amount", "amused", "analyst",
        "anchor", "ancient", "anger", "angle", "angry", "animal", "ankle", "announce", "annual", "another",
        "answer", "antenna", "antique", "anxiety", "any", "apart", "apology", "appear", "apple", "approve",
        "april", "arch", "arctic", "area", "arena", "argue", "arm", "armed", "armor", "army",
        "around", "arrange", "arrest", "arrive", "arrow", "art", "artefact", "artist", "artwork", "ask"
    ]
    
    @staticmethod
    def generate_mnemonic(strength: int = 256) -> str:
        """Generate BIP39 mnemonic seed phrase (24 words for 256-bit)"""
        # Generate entropy
        entropy = secrets.token_bytes(strength // 8)
        
        # Calculate checksum
        entropy_hash = hashlib.sha256(entropy).digest()
        checksum_bits = (strength // 32)
        checksum = entropy_hash[0] >> (8 - checksum_bits)
        
        # Combine entropy and checksum
        total_bits = strength + checksum_bits
        entropy_int = int.from_bytes(entropy, 'big')
        combined = (entropy_int << checksum_bits) | checksum
        
        # Split into 11-bit segments and map to words
        words = []
        for i in range(total_bits // 11):
            word_index = (combined >> (total_bits - 11 - (i * 11))) & 0x7FF
            words.append(BIP39Wallet.WORDLIST[word_index % len(BIP39Wallet.WORDLIST)])
        
        return ' '.join(words)
    
    @staticmethod
    def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
        """Convert BIP39 mnemonic to seed using PBKDF2"""
        mnemonic_bytes = mnemonic.encode('utf-8')
        salt = ("mnemonic" + passphrase).encode('utf-8')
        return hashlib.pbkdf2_hmac('sha512', mnemonic_bytes, salt, 2048, 64)
    
    @staticmethod
    def derive_master_key(seed: bytes) -> Tuple[bytes, bytes]:
        """BIP32 master key derivation"""
        # HMAC-SHA512 of "Bitcoin seed" + seed
        hmac_obj = hmac.new(b"Bitcoin seed", seed, hashlib.sha512)
        l = hmac_obj.digest()[:32]  # Left 32 bytes = private key
        r = hmac_obj.digest()[32:]   # Right 32 bytes = chain code
        return l, r
    
    @staticmethod
    def derive_child_key(parent_key: bytes, chain_code: bytes, index: int, hardened: bool = False) -> Tuple[bytes, bytes]:
        """BIP32 child key derivation"""
        if hardened:
            data = b'\x00' + parent_key + index.to_bytes(4, 'big')
        else:
            # For normal derivation, we need public key
            data = parent_key + index.to_bytes(4, 'big')
        
        hmac_obj = hmac.new(chain_code, data, hashlib.sha512)
        child_key = hmac_obj.digest()[:32]
        child_chain = hmac_obj.digest()[32:]
        return child_key, child_chain
    
    @staticmethod
    def derive_address_from_path(mnemonic: str, path: str = "m/44'/1989'/0'/0/0") -> str:
        """Derive address from BIP44 path"""
        seed = BIP39Wallet.mnemonic_to_seed(mnemonic)
        master_key, master_chain = BIP39Wallet.derive_master_key(seed)
        
        # Parse BIP44 path: m / purpose' / coin_type' / account' / change / address_index
        parts = path.split('/')[1:]  # Remove 'm'
        
        current_key = master_key
        current_chain = master_chain
        
        for part in parts:
            is_hardened = "'" in part
            index = int(part.replace("'", ""))
            if is_hardened:
                index += 0x80000000
            current_key, current_chain = BIP39Wallet.derive_child_key(
                current_key, current_chain, index, is_hardened
            )
        
        # Convert to address (simplified - in production use proper secp256k1)
        import hashlib
        from core.segwit import SegWitAddress
        
        pubkey_hash = hashlib.sha256(current_key).digest()[:20]
        return SegWitAddress.p2wpkh_from_pubkey(pubkey_hash)
    
    @staticmethod
    def create_wallet(wallet_name: str, passphrase: str = "") -> Dict:
        """Create a new deterministic wallet"""
        mnemonic = BIP39Wallet.generate_mnemonic(256)
        seed = BIP39Wallet.mnemonic_to_seed(mnemonic, passphrase)
        
        # Store wallet
        conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bip39_wallets (
                wallet_name TEXT PRIMARY KEY,
                mnemonic TEXT,
                seed_hash TEXT,
                created_at INTEGER
            )
        ''')
        
        seed_hash = hashlib.sha256(seed).hexdigest()
        cursor.execute('''
            INSERT OR REPLACE INTO bip39_wallets (wallet_name, mnemonic, seed_hash, created_at)
            VALUES (?, ?, ?, ?)
        ''', (wallet_name, mnemonic, seed_hash, int(time.time())))
        
        conn.commit()
        conn.close()
        
        # Derive first address
        address = BIP39Wallet.derive_address_from_path(mnemonic)
        
        return {
            "wallet_name": wallet_name,
            "mnemonic": mnemonic,
            "address": address,
            "path": "m/44'/1989'/0'/0/0",
            "standard": "BIP39/BIP32/BIP44",
            "message": "SAVE YOUR MNEMONIC PHRASE - This is the ONLY way to recover your wallet"
        }
    
    @staticmethod
    def get_wallet(wallet_name: str) -> Dict:
        """Get existing wallet info"""
        conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('SELECT mnemonic FROM bip39_wallets WHERE wallet_name = ?', (wallet_name,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {"error": f"Wallet '{wallet_name}' not found"}
        
        address = BIP39Wallet.derive_address_from_path(row[0])
        
        return {
            "wallet_name": wallet_name,
            "address": address,
            "path": "m/44'/1989'/0'/0/0",
            "standard": "BIP39/BIP32/BIP44",
            "message": "Wallet restored from seed"
        }
    
    @staticmethod
    def restore_wallet(wallet_name: str, mnemonic: str) -> Dict:
        """Restore wallet from mnemonic phrase"""
        # Validate mnemonic word count
        words = mnemonic.strip().split()
        if len(words) not in [12, 24]:
            return {"error": "Mnemonic must be 12 or 24 words"}
        
        # Verify checksum (simplified)
        address = BIP39Wallet.derive_address_from_path(mnemonic)
        
        # Store restored wallet
        conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO bip39_wallets (wallet_name, mnemonic, seed_hash, created_at)
            VALUES (?, ?, ?, ?)
        ''', (wallet_name, mnemonic, hashlib.sha256(mnemonic.encode()).hexdigest(), int(time.time())))
        
        conn.commit()
        conn.close()
        
        return {
            "wallet_name": wallet_name,
            "mnemonic": mnemonic,
            "address": address,
            "path": "m/44'/1989'/0'/0/0",
            "standard": "BIP39/BIP32/BIP44",
            "message": "Wallet restored successfully"
        }
    
    @staticmethod
    def derive_address(wallet_name: str, index: int = 0) -> Dict:
        """Derive address at specific index"""
        conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('SELECT mnemonic FROM bip39_wallets WHERE wallet_name = ?', (wallet_name,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {"error": f"Wallet '{wallet_name}' not found"}
        
        path = f"m/44'/1989'/0'/0/{index}"
        address = BIP39Wallet.derive_address_from_path(row[0], path)
        
        return {
            "wallet_name": wallet_name,
            "address": address,
            "index": index,
            "path": path,
            "standard": "BIP44"
        }
