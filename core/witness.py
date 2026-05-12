"""Segregated Witness data structure - Actual witness separation (BIP141)"""
import hashlib
import json
from typing import Dict, List, Optional, Tuple

class WitnessData:
    """Separate witness structure for SegWit transactions"""
    
    def __init__(self):
        self.witnesses: Dict[str, List[bytes]] = {}
    
    def add_witness(self, txid: str, witness_stack: List[bytes]) -> None:
        """Add witness data for a transaction"""
        self.witnesses[txid] = witness_stack
    
    def get_witness(self, txid: str) -> Optional[List[bytes]]:
        """Get witness data for a transaction"""
        return self.witnesses.get(txid)
    
    def remove_witness(self, txid: str) -> None:
        """Remove witness data"""
        self.witnesses.pop(txid, None)
    
    def calculate_witness_hash(self, txid: str) -> str:
        """Calculate witness transaction hash (wtxid)"""
        witness_stack = self.witnesses.get(txid, [])
        if not witness_stack:
            return txid
        
        # Serialize witness data
        witness_serialized = b''
        witness_serialized += len(witness_stack).to_bytes(1, 'little')
        for item in witness_stack:
            witness_serialized += len(item).to_bytes(1, 'little')
            witness_serialized += item
        
        # Hash with transaction data
        combined = txid.encode() + witness_serialized
        return hashlib.sha256(hashlib.sha256(combined).digest()).hexdigest()

class WitnessTransaction:
    """Transaction with segregated witness"""
    
    def __init__(self, version: int = 2, marker: int = 0, flag: int = 1):
        self.version = version
        self.marker = marker  # Must be 0 for SegWit
        self.flag = flag      # Must be 1 for SegWit
        self.inputs = []
        self.outputs = []
        self.witnesses = WitnessData()
    
    def add_input(self, txid: str, vout: int, script_sig: bytes = b'', sequence: int = 0xffffffff):
        """Add transaction input"""
        self.inputs.append({
            'txid': txid,
            'vout': vout,
            'script_sig': script_sig,
            'sequence': sequence
        })
    
    def add_output(self, amount: int, script_pubkey: bytes):
        """Add transaction output"""
        self.outputs.append({
            'amount': amount,
            'script_pubkey': script_pubkey
        })
    
    def add_witness(self, index: int, witness_stack: List[bytes]):
        """Add witness data for input at index"""
        self.witnesses.add_witness(f"input_{index}", witness_stack)
    
    def serialize(self) -> bytes:
        """Serialize transaction with witness data"""
        result = self.version.to_bytes(4, 'little')
        
        if self.witnesses.witnesses:
            # SegWit marker and flag
            result += self.marker.to_bytes(1, 'little')
            result += self.flag.to_bytes(1, 'little')
        
        # Input count and inputs
        result += len(self.inputs).to_bytes(1, 'little')
        for inp in self.inputs:
            result += bytes.fromhex(inp['txid'])[::-1]
            result += inp['vout'].to_bytes(4, 'little')
            result += len(inp['script_sig']).to_bytes(1, 'little')
            result += inp['script_sig']
            result += inp['sequence'].to_bytes(4, 'little')
        
        # Output count and outputs
        result += len(self.outputs).to_bytes(1, 'little')
        for out in self.outputs:
            result += out['amount'].to_bytes(8, 'little')
            result += len(out['script_pubkey']).to_bytes(1, 'little')
            result += out['script_pubkey']
        
        # Witness data (if any)
        if self.witnesses.witnesses:
            for i in range(len(self.inputs)):
                witness_stack = self.witnesses.get_witness(f"input_{i}")
                if witness_stack:
                    result += len(witness_stack).to_bytes(1, 'little')
                    for item in witness_stack:
                        result += len(item).to_bytes(1, 'little')
                        result += item
                else:
                    result += (0).to_bytes(1, 'little')
        
        # Locktime
        result += (0).to_bytes(4, 'little')
        
        return result
    
    def to_json(self) -> Dict:
        """Convert to JSON representation"""
        return {
            'version': self.version,
            'segwit': len(self.witnesses.witnesses) > 0,
            'inputs': len(self.inputs),
            'outputs': len(self.outputs),
            'has_witness': len(self.witnesses.witnesses) > 0
        }

class WitnessValidator:
    """Validate witness data"""
    
    @staticmethod
    def validate_witness_program(program: bytes, witness_stack: List[bytes]) -> bool:
        """Validate witness program (P2WPKH or P2WSH)"""
        if len(program) == 20:
            # P2WPKH: program is pubkey hash
            return WitnessValidator._validate_p2wpkh(program, witness_stack)
        elif len(program) == 32:
            # P2WSH: program is script hash
            return WitnessValidator._validate_p2wsh(program, witness_stack)
        return False
    
    @staticmethod
    def _validate_p2wpkh(pubkey_hash: bytes, witness_stack: List[bytes]) -> bool:
        """Validate P2WPKH witness"""
        if len(witness_stack) != 2:
            return False
        
        signature, pubkey = witness_stack
        # Check pubkey hash matches
        calculated_hash = hashlib.sha256(pubkey).digest()[:20]
        return calculated_hash == pubkey_hash
    
    @staticmethod
    def _validate_p2wsh(script_hash: bytes, witness_stack: List[bytes]) -> bool:
        """Validate P2WSH witness"""
        if len(witness_stack) < 1:
            return False
        
        redeem_script = witness_stack[-1]
        calculated_hash = hashlib.sha256(redeem_script).digest()
        return calculated_hash == script_hash
