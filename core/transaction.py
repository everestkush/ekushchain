import hashlib
import json
import time
from core.wallet import EKUSHWallet
from core.system_config import SYSTEM_ADDRESS, SYSTEM_PUBLIC_KEY, SYSTEM_PRIVATE_KEY

class EKUSHTransaction:
    def __init__(self, sender: str, recipient: str, amount: float, fee: float, timestamp: float = None, replaceable: bool = True, public_key: str = None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.fee = fee
        self.timestamp = timestamp if timestamp else time.time()
        self.signature = None
        self.is_system = False
        self.replaceable = replaceable
        self.public_key = public_key

    def calculate_hash(self) -> str:
        data = json.dumps({
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "fee": self.fee,
            "timestamp": self.timestamp,
            "replaceable": self.replaceable,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def sign(self, private_key_bytes: bytes):
        """Sign transaction with real ECDSA (secp256k1)"""
        from ecdsa import SigningKey, SECP256k1
        from coincurve import PrivateKey
        tx_hash = self.calculate_hash()
        sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
        # Derive and store public key
        self.public_key = sk.get_verifying_key().to_string().hex()
        self.signature = sk.sign(tx_hash.encode())
    def verify(self) -> bool:
        """Verify transaction signature using real ECDSA (secp256k1)"""
        if self.is_system:
            return True
        if self.sender == "EverestKush_Genesis":
            return True
        if self.sender == SYSTEM_ADDRESS:
            return True
        
        if not self.signature or len(self.signature) < 32:
            print(f"[ERROR] Invalid signature: missing or too short")
            return False
        
        if not self.public_key:
            print(f"[ERROR] Cannot verify: no public key provided for {self.sender[:16]}")
            return False
        
        try:
            from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
            tx_hash = self.calculate_hash()
            vk = VerifyingKey.from_string(bytes.fromhex(self.public_key), curve=SECP256k1)
            vk.verify(self.signature, tx_hash.encode())
            return True
        except BadSignatureError:
            print(f"[ERROR] Invalid signature for tx from {self.sender[:16]}")
            return False
        except Exception as e:
            print(f"[ERROR] Verification error: {e}")
            return False
    def validate_script(self, script_sig, script_pubkey):
        """Validate Bitcoin-style script (simplified for EverestKush)"""
        if not self.signature:
            return False
        return self.verify()

    def to_dict(self):
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "fee": self.fee,
            "timestamp": self.timestamp,
            "signature": self.signature.hex() if self.signature else None,
            "replaceable": self.replaceable,
        }

    def __repr__(self):
        return f"TX {self.calculate_hash()[:16]}... | {self.sender[:16]}... -> {self.recipient[:16]}... | {self.amount} EKUSH"

    # OP_RETURN support for data storage (80 bytes max)
    OP_RETURN = "6a"
    MAX_OP_RETURN_SIZE = 80  # bytes

    def add_op_return(self, data: bytes):
        """Add OP_RETURN data to transaction (Bitcoin standard)"""
        if len(data) > self.MAX_OP_RETURN_SIZE:
            raise ValueError(f"OP_RETURN data exceeds {self.MAX_OP_RETURN_SIZE} bytes")
        
        # Encode data as hex
        data_hex = data.hex()
        self.op_return_data = data_hex
        self.is_op_return = True
    
    def get_op_return_data(self):
        """Get OP_RETURN data from transaction"""
        return bytes.fromhex(self.op_return_data) if hasattr(self, 'op_return_data') else None

    def add_op_return(self, data: bytes):
        """Add OP_RETURN data to transaction (Bitcoin standard)"""
        if len(data) > 80:
            raise ValueError(f"OP_RETURN data exceeds 80 bytes")
        self.op_return_data = data.hex()
        self.is_op_return = True
    
    def get_op_return_data(self):
        """Get OP_RETURN data from transaction"""
        return bytes.fromhex(self.op_return_data) if hasattr(self, 'op_return_data') else None

    def add_op_return(self, data: bytes):
        """Add OP_RETURN data (max 80 bytes)"""
        if len(data) > 80:
            raise ValueError("OP_RETURN data exceeds 80 bytes")
        self.op_return_data = data.hex()
        self.is_op_return = True
    
    def get_op_return(self):
        return bytes.fromhex(self.op_return_data) if hasattr(self, 'op_return_data') else None

    # Dust limit (Bitcoin standard: 546 satoshis = 0.00000546)
    DUST_LIMIT = 0.00000546

    def is_dust(self) -> bool:
        """Check if transaction output is dust (economically pointless)"""
        return self.amount < self.DUST_LIMIT

    # Timelock support (CLTV/CSV)
    def set_locktime(self, locktime: int, is_block_height: bool = True):
        """Set transaction locktime (CLTV)"""
        self.locktime = locktime
        self.locktime_is_height = is_block_height
    
    def is_timelocked(self, current_height: int, current_time: int) -> bool:
        """Check if timelock condition is satisfied"""
        if not hasattr(self, 'locktime'):
            return True
        if self.locktime_is_height:
            return current_height >= self.locktime
        else:
            return current_time >= self.locktime

    # Transaction version (for upgrades)
    TX_VERSION = 1
    
    def set_version(self, version: int):
        """Set transaction version"""
        self.tx_version = version
    
    def get_version(self) -> int:
        return getattr(self, 'tx_version', self.TX_VERSION)
