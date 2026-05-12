import hashlib
from typing import List
"""Native SegWit (P2WPKH) support - BIP141, BIP173, BIP350"""
import hashlib
import base58
from typing import Tuple, Optional

class SegWitAddress:
    """Native SegWit address generation and validation (bech32)"""
    
    # EverestKush human readable part (like Bitcoin's 'bc')
    HRP = "ekush"
    
    @staticmethod
    def p2wpkh_from_pubkey(pubkey_hash: bytes) -> str:
        """Convert public key hash to P2WPKH bech32 address"""
        # witness program = 0x00 (version 0) + 20-byte pubkey hash
        witness_program = b'\x00' + pubkey_hash
        return SegWitAddress._bech32_encode(witness_program)
    
    @staticmethod
    def p2wpkh_from_address(legacy_address: str) -> Optional[str]:
        """Convert legacy address to native SegWit address"""
        # Decode legacy address
        decoded = base58.b58decode_check(legacy_address)
        if len(decoded) != 21 or decoded[0] != 0:
            return None
        pubkey_hash = decoded[1:]
        return SegWitAddress.p2wpkh_from_pubkey(pubkey_hash)
    
    @staticmethod
    def _bech32_encode(witness_program: bytes) -> str:
        """Bech32 encoding for native SegWit addresses"""
        # Simplified bech32 - for production, use full implementation
        from bech32 import bech32_encode, convertbits
        data = convertbits(witness_program, 8, 5)
        return bech32_encode(SegWitAddress.HRP, data)
    
    @staticmethod
    def validate(address: str) -> Tuple[bool, Optional[str]]:
        """Validate native SegWit address"""
        if not address.startswith(SegWitAddress.HRP + "1"):
            return False, "Not a native SegWit address"
        
        # Basic length check
        if len(address) < 14 or len(address) > 74:
            return False, "Invalid address length"
        
        return True, None
    
    @staticmethod
    def get_witness_program(address: str) -> Optional[bytes]:
        """Extract witness program from address"""
        from bech32 import bech32_decode, convertbits
        hrp, data = bech32_decode(address)
        if hrp != SegWitAddress.HRP or not data:
            return None
        return bytes(convertbits(data, 5, 8) or [])

# ========== P2WSH (SegWit Script Addresses) ==========

class P2WSH:
    """Pay-to-Witness-Script-Hash (SegWit script addresses)"""
    
    @staticmethod
    def from_script(script: bytes) -> str:
        """Create P2WSH address from redeem script"""
        # SHA256 of the script (32 bytes for P2WSH)
        script_hash = hashlib.sha256(script).digest()
        # Witness program: version 0 (0x00) + 32-byte script hash
        witness_program = b'\x00' + script_hash
        return SegWitAddress._bech32_encode(witness_program)
    
    @staticmethod
    def from_multisig(public_keys: List[str], required: int) -> str:
        """Create P2WSH address from multisig"""
        # Create multisig redeem script
        from core.script import ScriptBuilder
        
        builder = ScriptBuilder()
        builder.append_number(required)
        for pubkey in public_keys:
            builder.append_data(bytes.fromhex(pubkey))
        builder.append_number(len(public_keys))
        builder.append_opcode('OP_CHECKMULTISIG')
        
        return P2WSH.from_script(builder.build())
    
    @staticmethod
    def validate(witness_program: bytes, witness_stack: List[bytes]) -> bool:
        """Validate P2WSH witness"""
        if len(witness_program) != 33 or witness_program[0] != 0:
            return False
        
        script_hash = witness_program[1:33]
        redeem_script = witness_stack[-1]
        
        # Verify redeem script matches hash
        return hashlib.sha256(redeem_script).digest() == script_hash
