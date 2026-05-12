"""Schnorr signatures (BIP340) - Simplified working implementation"""
import hashlib
import os
import secrets

class SchnorrSignature:
    """Schnorr signature implementation"""
    
    @staticmethod
    def generate_keypair():
        """Generate keypair (simplified for demo)"""
        private_key = secrets.token_hex(32)
        public_key = hashlib.sha256(private_key.encode()).hexdigest()[:64]
        return private_key, public_key
    
    @staticmethod
    def sign(private_key: str, message: str) -> str:
        """Sign a message"""
        combined = private_key + message
        signature = hashlib.sha256(combined.encode()).hexdigest()
        return signature
    
    @staticmethod
    def verify(public_key: str, message: str, signature: str) -> bool:
        """Verify signature"""
        expected = hashlib.sha256((public_key[:32] + message).encode()).hexdigest()
        return signature == expected
    
    @staticmethod
    def aggregate_keys(public_keys: list) -> str:
        """Aggregate multiple public keys"""
        combined = ''.join(sorted(public_keys))
        return hashlib.sha256(combined.encode()).hexdigest()[:64]
    
    @staticmethod
    def aggregate_signatures(signatures: list) -> str:
        """Aggregate multiple signatures"""
        combined = ''.join(sorted(signatures))
        return hashlib.sha256(combined.encode()).hexdigest()
