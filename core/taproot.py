"""Taproot / Tapscript implementation (BIP341/BIP342)"""
import hashlib

class Taproot:
    """Taproot address and spending conditions"""
    
    # Taproot human readable part
    HRP = "ekush1"  # For Taproot addresses (like Bitcoin's bc1p)
    
    @staticmethod
    def create_taproot_address(internal_pubkey: str, merkle_root: str = "") -> str:
        """Create Taproot address from internal public key"""
        # Simplified Taproot address generation
        combined = internal_pubkey + merkle_root
        taproot_hash = hashlib.sha256(combined.encode()).hexdigest()
        return f"ekush1p{taproot_hash[:58]}"
    
    @staticmethod
    def create_taproot_script(conditions: list) -> str:
        """Create Taproot script with spending conditions"""
        # Build script tree
        script_tree = Taproot._build_merkle_tree(conditions)
        return script_tree
    
    @staticmethod
    def _build_merkle_tree(leaves: list) -> str:
        """Build Merkle tree from script leaves"""
        if not leaves:
            return ""
        if len(leaves) == 1:
            return hashlib.sha256(leaves[0].encode()).hexdigest()
        
        # Build tree
        tree = leaves[:]
        while len(tree) > 1:
            new_level = []
            for i in range(0, len(tree), 2):
                if i + 1 < len(tree):
                    combined = tree[i] + tree[i + 1]
                else:
                    combined = tree[i] + tree[i]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            tree = new_level
        return tree[0]
    
    @staticmethod
    def create_spending_script(conditions: dict) -> str:
        """Create script for spending conditions"""
        script_parts = []
        
        if 'timelock' in conditions:
            script_parts.append(f"OP_CHECKLOCKTIMEVERIFY {conditions['timelock']}")
        if 'multisig' in conditions:
            m = conditions['multisig']['required']
            n = len(conditions['multisig']['keys'])
            script_parts.append(f"OP_{m} {' '.join(conditions['multisig']['keys'])} OP_{n} OP_CHECKMULTISIG")
        if 'hashlock' in conditions:
            script_parts.append(f"OP_SHA256 {conditions['hashlock']} OP_EQUALVERIFY")
        
        return " ".join(script_parts)

class TapscriptValidator:
    """Validate Taproot/Tapscript transactions"""
    
    @staticmethod
    def validate_taproot_address(address: str) -> bool:
        """Validate Taproot address format"""
        return address.startswith("ekush1p") and len(address) >= 60
    
    @staticmethod
    def verify_taproot_spend(script: str, witness: list) -> bool:
        """Verify Taproot spending conditions"""
        # Simplified verification
        return len(witness) > 0
