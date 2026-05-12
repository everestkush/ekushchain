"""
P2SH Multisig - Bitcoin Standard (BIP16)
M-of-N signature requirements for enhanced security
"""

import hashlib
import base58
from typing import List

class MultisigAddress:
    def __init__(self, m: int, public_keys: List[str]):
        self.m = m
        self.n = len(public_keys)
        self.public_keys = sorted(public_keys)
        
        if m > self.n:
            raise ValueError(f"m ({m}) cannot be greater than n ({self.n})")
        
        self.redeem_script = self._create_redeem_script()
        self.address = self._create_p2sh_address()
    
    def _create_redeem_script(self) -> str:
        op_codes = {1: "51", 2: "52", 3: "53", 4: "54", 5: "55",
                    6: "56", 7: "57", 8: "58", 9: "59", 10: "5a",
                    11: "5b", 12: "5c", 13: "5d", 14: "5e", 15: "5f"}
        OP_CHECKMULTISIG = "ae"
        
        m_op = op_codes.get(self.m, "51")
        n_op = op_codes.get(self.n, "51")
        
        script = m_op
        for pubkey in self.public_keys:
            clean_key = pubkey[:66] if len(pubkey) > 66 else pubkey
            script += "21" + clean_key
        script += n_op + OP_CHECKMULTISIG
        return script
    
    def _create_p2sh_address(self) -> str:
        sha256 = hashlib.sha256(bytes.fromhex(self.redeem_script)).digest()
        ripemd160 = hashlib.new('ripemd160', sha256).digest()
        versioned = b'\x05' + ripemd160
        checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
        return base58.b58encode(versioned + checksum).decode()
    
    def get_info(self) -> dict:
        return {
            "type": "P2SH_Multisig",
            "required": self.m,
            "total": self.n,
            "address": self.address,
            "redeem_script": self.redeem_script,
            "standard": "BIP16"
        }


def create_multisig_address(m: int, public_keys: List[str]) -> dict:
    try:
        return MultisigAddress(m, public_keys).get_info()
    except Exception as e:
        return {"error": str(e)}
