"""
BIP32: Hierarchical Deterministic Wallets
Purpose: One master seed controls unlimited child wallets

Key Concepts:
- xprv: Extended Private Key (FULL control - KEEP SECRET!)
- xpub: Extended Public Key (View-only - CAN SHARE)
- Hardened Derivation ('): Prevents parent key leakage
"""

import hashlib
import hmac
import base58
from bip32utils import BIP32Key, BIP32_HARDEN

class BIP32Wallet:
    """BIP32 Standard - HD Wallet"""
    
    # BIP44 Path for EverestKush
    # m / purpose' / coin_type' / account' / change / address_index
    # m / 44'    / 1989'      / 0'       / 0      / 0          = First address
    
    COIN_TYPE = 1989  # Nepal's country code
    PURPOSE = 44      # BIP44
    
    def __init__(self, seed_hex):
        """
        Initialize HD wallet from seed
        seed_hex: hex string from BIP39 mnemonic
        """
        seed = bytes.fromhex(seed_hex)
        self.master_key = BIP32Key.fromEntropy(seed)
        
        # Generate xpub (extended public key) - shareable
        self.xpub = self.master_key.ExtendedKey()
        
        # Generate xprv (extended private key) - SECRET!
        self.xprv = self.master_key.ExtendedKey(private=True)
    
    def derive_path(self, path):
        """
        Derive key at specific BIP32 path
        
        Example: "m/44'/1989'/0'/0/0"
        ' = hardened derivation
        """
        key = self.master_key
        parts = path.split('/')[1:]  # Remove 'm/'
        
        for part in parts:
            if part.endswith("'"):
                # Hardened derivation
                child_num = int(part[:-1]) | BIP32_HARDEN
            else:
                # Normal derivation
                child_num = int(part)
            key = key.ChildKey(child_num)
        
        return key
    
    def get_address(self, account=0, change=0, index=0):
        """
        Get address following BIP44 standard
        Path: m/44'/1989'/account'/change/index
        """
        path = f"m/44'/{self.COIN_TYPE}'/{account}'/{change}/{index}"
        key = self.derive_path(path)
        return key.Address()
    
    def get_private_key(self, account=0, change=0, index=0):
        """Get private key for spending"""
        path = f"m/44'/{self.COIN_TYPE}'/{account}'/{change}/{index}"
        key = self.derive_path(path)
        return key.PrivateKey().hex()
    
    def get_public_key(self, account=0, change=0, index=0):
        """Get public key for verification"""
        path = f"m/44'/{self.COIN_TYPE}'/{account}'/{change}/{index}"
        key = self.derive_path(path)
        return key.PublicKey().hex()
    
    def generate_addresses(self, count=10, account=0, change=0):
        """Generate multiple addresses"""
        addresses = []
        for i in range(count):
            addresses.append({
                "index": i,
                "path": f"m/44'/{self.COIN_TYPE}'/{account}'/{change}/{i}",
                "address": self.get_address(account, change, i),
                "private_key": self.get_private_key(account, change, i),
                "public_key": self.get_public_key(account, change, i)
            })
        return addresses
    
    def get_watch_only_wallet(self):
        """
        Return xpub for watch-only wallet
        Anyone with xpub can SEE transactions but cannot SPEND
        """
        return {
            "xpub": self.xpub,
            "type": "watch_only",
            "capabilities": ["view_balance", "view_transactions", "generate_addresses"],
            "cannot": ["send_transactions", "sign_messages"]
        }
    
    def export_wallet(self):
        """Export full wallet for backup"""
        return {
            "xpub": self.xpub,
            "xprv": self.xprv,  # WARNING: This is secret!
            "type": "full_control",
            "coin_type": self.COIN_TYPE,
            "standard": "BIP32/BIP44"
        }


# BIP44 Standard Paths
BIP44_PATHS = {
    "receive": "m/44'/1989'/0'/0",      # Receiving addresses
    "change": "m/44'/1989'/0'/1",       # Change addresses (internal)
    "staking": "m/44'/1989'/1'/0/0",    # Validator staking
    "airdrop": "m/44'/1989'/2'/0/0",    # Airdrop distribution
}
