"""
PSBT - Partially Signed Bitcoin Transactions (BIP174)
Allows multiple parties to sign a transaction
"""

import json
import time

class PSBT:
    def __init__(self, inputs, outputs):
        self.inputs = inputs
        self.outputs = outputs
        self.signatures = []
        self.created_at = time.time()
        self.finalized = False
    
    def add_signature(self, signature, public_key):
        """Add a partial signature"""
        self.signatures.append({
            "signature": signature.hex() if hasattr(signature, 'hex') else signature,
            "public_key": public_key,
            "timestamp": time.time()
        })
        return len(self.signatures)
    
    def is_ready(self, required_signatures):
        """Check if enough signatures are collected"""
        return len(self.signatures) >= required_signatures
    
    def finalize(self):
        """Finalize the PSBT for broadcast"""
        if self.is_ready(len(self.inputs)):
            self.finalized = True
            return self.to_transaction()
        return None
    
    def to_dict(self):
        return {
            "inputs": self.inputs,
            "outputs": self.outputs,
            "signatures": self.signatures,
            "created_at": self.created_at,
            "finalized": self.finalized
        }
    
    def to_transaction(self):
        """Convert to executable transaction"""
        # Simplified - in production, build actual transaction
        return {"psbt_finalized": True, "signatures": len(self.signatures)}
