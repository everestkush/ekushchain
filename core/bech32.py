"""
Bech32 address format for EKUSH (BIP173)
HRP: ekush
"""
import bech32
import hashlib
import secrets
from ecdsa import SigningKey, SECP256k1

HRP = "ekush"

def encode_public_key(public_key_bytes) -> str:
    """Encode public key to bech32 address"""
    sha = hashlib.sha256(public_key_bytes).digest()
    witness_program = hashlib.new('ripemd160', sha).digest()
    return bech32.bech32_encode(HRP, bech32.convertbits(witness_program, 8, 5))

def encode_script_hash(script_hash_bytes) -> str:
    """Encode script hash to bech32 address"""
    return bech32.bech32_encode(HRP, bech32.convertbits(script_hash_bytes[:20], 8, 5))

def decode_address(address: str) -> tuple:
    """Decode bech32 address to witness program"""
    hrp, data = bech32.bech32_decode(address)
    if hrp != HRP:
        raise ValueError(f"Invalid HRP: expected {HRP}, got {hrp}")
    return bech32.convertbits(data, 5, 8)

def generate_wallet() -> dict:
    """Generate new wallet with bech32 address"""
    private_key = secrets.token_bytes(32)
    sk = SigningKey.from_string(private_key, curve=SECP256k1)
    public_key = sk.get_verifying_key().to_string()
    address = encode_public_key(public_key)
    
    return {
        "address": address,
        "private_key": private_key.hex(),
        "public_key": public_key.hex(),
        "hrp": HRP
    }

def validate_address(address: str) -> bool:
    """Validate bech32 address format"""
    try:
        hrp, data = bech32.bech32_decode(address)
        if hrp != HRP or not data:
            return False
        return True
    except:
        return False
