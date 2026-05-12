import ecdsa
import hashlib
import base58
import json
from dataclasses import dataclass
from typing import Tuple

class EKUSHWallet:
    """EverestKush Wallet - Generate keys and addresses like Bitcoin"""
    
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.address = None
    
    def generate(self):
        """Generate a new wallet key pair"""
        # Generate private key (secp256k1 - same as Bitcoin)
        self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.public_key = self.private_key.get_verifying_key()
        self.address = self._generate_address()
        return self
    
    def _generate_address(self) -> str:
        """Generate EKUSH address from public key"""
        # Step 1: Get public key bytes
        public_key_bytes = self.public_key.to_string()
        
        # Step 2: SHA-256 hash of public key
        sha256_hash = hashlib.sha256(public_key_bytes).digest()
        
        # Step 3: RIPEMD-160 hash (for shorter address)
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_hash)
        hashed_public_key = ripemd160.digest()
        
        # Step 4: Add version byte (0x00 for mainnet, we'll use 0x45 for EKUSH)
        versioned_payload = b'\x45' + hashed_public_key  # 0x45 = 'E' for EverestKush
        
        # Step 5: Double SHA-256 for checksum
        checksum = hashlib.sha256(hashlib.sha256(versioned_payload).digest()).digest()[:4]
        
        # Step 6: Base58 encode (like Bitcoin addresses)
        address_bytes = versioned_payload + checksum
        self.address = base58.b58encode(address_bytes).decode('utf-8')
        
        return self.address
    
    def get_private_key_hex(self) -> str:
        """Export private key as hex string"""
        return self.private_key.to_string().hex()
    
    def get_public_key_hex(self) -> str:
        """Export public key as hex string"""
        return self.public_key.to_string().hex()
    
    def sign_transaction(self, transaction_hash: str) -> bytes:
        """Sign a transaction hash with private key"""
        signature = self.private_key.sign(transaction_hash.encode())
        return signature
    
    @staticmethod
    def import_from_private_key(private_key_hex: str):
        """Create wallet from existing private key"""
        wallet = EKUSHWallet()
        wallet.private_key = ecdsa.SigningKey.from_string(
            bytes.fromhex(private_key_hex), 
            curve=ecdsa.SECP256k1
        )
        wallet.public_key = wallet.private_key.get_verifying_key()
        wallet.address = wallet._generate_address()
        return wallet
    
    def to_dict(self):
        """Export wallet data (NEVER share private key!)"""
        return {
            "address": self.address,
            "public_key": self.get_public_key_hex(),
            "private_key": self.get_private_key_hex()  # Keep this safe!
        }
    
    def __repr__(self):
        return f"EKUSHWallet(address={self.address[:10]}...)"

    def rotate_key(self, new_private_key_hex):
        """Rotate to a new key while preserving address history"""
        try:
            new_wallet = EKUSHWallet.import_from_private_key(new_private_key_hex)
            self.rotation_history.append({
                "old_address": self.address,
                "new_address": new_wallet.address,
                "rotated_at": time.time()
            })
            self.private_key = new_private_key_hex
            self.address = new_wallet.address
            self.public_key = new_wallet.get_public_key_hex()
            return True
        except Exception as e:
            print(f"Key rotation failed: {e}")
            return False
    
    def get_rotation_history(self):
        """Get key rotation history"""
        return getattr(self, 'rotation_history', [])

# ========== NATIVE SEGWIT SUPPORT ==========
from core.segwit import SegWitAddress

def generate_segwit_address(self, pubkey_hash: bytes) -> str:
    """Generate native SegWit address (P2WPKH)"""
    return SegWitAddress.p2wpkh_from_pubkey(pubkey_hash)

def is_segwit_address(address: str) -> bool:
    """Check if address is native SegWit"""
    return address.startswith("ekush1")
