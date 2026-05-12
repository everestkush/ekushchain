"""
Checkpoints - Bitcoin Standard
Hardcoded block hashes to prevent deep chain reorganizations
"""

# Format: block_height: "block_hash"
CHECKPOINTS = {
    0: "29f7af0b3a6321efba98b1466d8a54ee0197242acb57402ecbe32bc20b0bd9be",  # Genesis
    1000: None,  # To be filled after mainnet reaches block 1000
    5000: None,  # To be filled after mainnet reaches block 5000
    10000: None, # To be filled after mainnet reaches block 10000
    50000: None, # To be filled after mainnet reaches block 50000
    100000: None, # To be filled after mainnet reaches block 100000
}

def verify_checkpoint(block_index, block_hash):
    """Verify if a block matches the hardcoded checkpoint"""
    if block_index in CHECKPOINTS and CHECKPOINTS[block_index]:
        if block_hash != CHECKPOINTS[block_index]:
            raise Exception(f"[ERROR] CHECKPOINT MISMATCH at block {block_index}!")
        print(f"[OK] Checkpoint verified: block {block_index}")
    return True

def add_checkpoint(block_index, block_hash):
    """Add a new checkpoint (only for development)"""
    CHECKPOINTS[block_index] = block_hash
    print(f"[OK] Checkpoint added: block {block_index} = {block_hash[:16]}...")

def get_checkpoint_info():
    """Get checkpoint information"""
    checkpoints = []
    for height, hash_val in CHECKPOINTS.items():
        if hash_val:
            checkpoints.append({"height": height, "hash": hash_val[:16] + "..."})
    return {"checkpoints": checkpoints, "total": len(checkpoints)}
"""
Finality Checkpoints - Bitcoin Standard
Automatic checkpoint updates for fork protection
"""

import json
import os

CHECKPOINTS_FILE = "checkpoints.json"

# Hardcoded genesis checkpoint
CHECKPOINTS = {
    0: "29f7af0b3a6321efba98b1466d8a54ee0197242acb57402ecbe32bc20b0bd9be",
}

def load_checkpoints():
    """Load checkpoints from file"""
    global CHECKPOINTS
    if os.path.exists(CHECKPOINTS_FILE):
        try:
            with open(CHECKPOINTS_FILE, 'r') as f:
                loaded = json.load(f)
                CHECKPOINTS.update(loaded)
        except:
            pass

def save_checkpoint(block_height, block_hash):
    """Save a new checkpoint automatically"""
    CHECKPOINTS[block_height] = block_hash
    try:
        with open(CHECKPOINTS_FILE, 'w') as f:
            json.dump(CHECKPOINTS, f, indent=2)
        print(f"[OK] Checkpoint saved: block {block_height}")
    except Exception as e:
        print(f"Failed to save checkpoint: {e}")

def add_auto_checkpoint(block_height, block_hash):
    """Automatically add checkpoint every 1000 blocks"""
    if block_height > 0 and block_height % 1000 == 0:
        save_checkpoint(block_height, block_hash)
        return True
    return False

def verify_checkpoint(block_index, block_hash):
    """Verify if a block matches the checkpoint"""
    if block_index in CHECKPOINTS:
        if block_hash != CHECKPOINTS[block_index]:
            raise Exception(f"[ERROR] CHECKPOINT MISMATCH at block {block_index}!")
        print(f"[OK] Checkpoint verified: block {block_index}")
        return True
    return True

def get_checkpoint_info():
    """Get checkpoint information"""
    checkpoints = []
    for height, hash_val in CHECKPOINTS.items():
        checkpoints.append({"height": height, "hash": hash_val[:16] + "..."})
    return {"checkpoints": checkpoints, "total": len(checkpoints)}
