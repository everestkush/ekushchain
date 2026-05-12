import os
import hashlib
import json
import time
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(__import__("os").environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
from typing import List, Optional
from collections import defaultdict
from core.transaction import EKUSHTransaction, SYSTEM_ADDRESS
from core import storage
from core.difficulty import DifficultyAdjustment
from core.checkpoints import verify_checkpoint, get_checkpoint_info

class EKUSHBlock:
    def __init__(self, index: int, transactions: List[EKUSHTransaction], previous_hash: str, validator: str = "genesis", difficulty: int = 1):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.validator = validator
        self.nonce = 0
        self.difficulty = difficulty
        self.merkle_root = self.calculate_merkle_root()
        self.hash = self.calculate_hash()

    def calculate_merkle_root(self) -> str:
        if not self.transactions:
            return "0" * 64
        tx_hashes = [tx.calculate_hash() for tx in self.transactions]
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 == 1:
                tx_hashes.append(tx_hashes[-1])
            tx_hashes = [hashlib.sha256((tx_hashes[i] + tx_hashes[i+1]).encode()).hexdigest()
                        for i in range(0, len(tx_hashes), 2)]
        return tx_hashes[0]

    def calculate_hash(self) -> str:
        data = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "previous_hash": self.previous_hash,
            "validator": self.validator,
            "difficulty": self.difficulty,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_transactions(self) -> bool:
        for tx in self.transactions:
            if not tx.verify():
                print(f"Invalid transaction in block {self.index}")
                return False
        return True
    def validate_block(self, blockchain) -> bool:
        """Full block validation before accepting"""
        # 1. Check block index matches chain
        if self.index != len(blockchain.chain):
            print(f"[ERROR] Block {self.index} has wrong index")
            return False
        
        # 2. Check previous hash matches
        if self.index > 0 and self.previous_hash != blockchain.chain[-1].hash:
            print(f"[ERROR] Block {self.index} has wrong previous hash")
            return False
        
        # 3. Check timestamp is within 2 hours of now
        if abs(self.timestamp - time.time()) > 7200:
            print(f"[ERROR] Block {self.index} timestamp too far in future/past")
            return False
        
        # 4. Check merkle root matches transactions
        computed_root = self.calculate_merkle_root()
        if self.merkle_root != computed_root:
            print(f"[ERROR] Block {self.index} invalid merkle root")
            return False
        
        # 5. Verify all transactions
        if not self.verify_transactions():
            print(f"[ERROR] Block {self.index} has invalid transactions")
            return False
        
        # 6. Check difficulty requirement
        if int(self.hash, 16) > 2**(256 - self.difficulty):
            print(f"[ERROR] Block {self.index} does not meet difficulty")
            return False
        
        # 7. Validate coinbase transaction
        if not blockchain.validate_coinbase_transaction(self.transactions[0]):
            print(f"[ERROR] Block {self.index} invalid coinbase")
            return False
        
        return True

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "validator": self.validator,
            "hash": self.hash,
            "merkle_root": self.merkle_root,
            "difficulty": self.difficulty
        }

    def __repr__(self):
        return f"Block #{self.index} | Hash: {self.hash[:16]}... | TXs: {len(self.transactions)} | Diff: {self.difficulty}"

    def get_merkle_proof(self, tx_hash):
        if not self.transactions:
            return None
        tx_hashes = [tx.calculate_hash() for tx in self.transactions]
        try:
            tx_index = tx_hashes.index(tx_hash)
        except ValueError:
            return None
        proof = []
        current_level = tx_hashes.copy()
        current_index = tx_index
        while len(current_level) > 1:
            if len(current_level) % 2 == 1:
                current_level.append(current_level[-1])
            if current_index % 2 == 0:
                sibling_index = current_index + 1
                position = "right"
            else:
                sibling_index = current_index - 1
                position = "left"
            if sibling_index < len(current_level):
                proof.append({"hash": current_level[sibling_index], "position": position})
            next_level = []
            for i in range(0, len(current_level), 2):
                combined = current_level[i] + current_level[i+1]
                parent = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(parent)
            current_level = next_level
            current_index = current_index // 2
        return {
            "tx_hash": tx_hash,
            "merkle_root": self.merkle_root,
            "proof": proof,
            "block_index": self.index,
            "block_hash": self.hash
        }

    def verify_merkle_proof(self, tx_hash, proof, merkle_root):
        current_hash = tx_hash
        for step in proof:
            if step["position"] == "left":
                combined = step["hash"] + current_hash
            else:
                combined = current_hash + step["hash"]
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
        return current_hash == merkle_root


class EKUSHChain:
    def __init__(self):
        self.difficulty = 1
        self.difficulty_adjuster = DifficultyAdjustment()
        self.MAX_MEMPOOL_SIZE = 10000
        self.MAX_BLOCK_WEIGHT = 4000000
        self.MAX_BLOCK_SIZE = 1000000
        self.COINBASE_MATURITY = 100

        self.utxo_set = {}
        self.spent_outputs = set()

        self._init_balance_db()

        if not storage.chain_exists():
            storage.init_db()
            genesis = self._genesis()
            self.chain = [genesis]
            storage.save_block(genesis)
            self._update_balance(SYSTEM_ADDRESS, 0)
        else:
            self.chain = []
            blocks_data = storage.load_chain()
            for block_data in blocks_data:
                transactions = block_data["transactions"]
                block = EKUSHBlock(
                    index=block_data["index"],
                    transactions=transactions,
                    previous_hash=block_data["previous_hash"],
                    validator=block_data["validator"],
                    difficulty=block_data.get("difficulty", 1)
                )
                block.timestamp = block_data["timestamp"]
                block.nonce = block_data["nonce"]
                block.hash = block_data["hash"]
                block.merkle_root = block.calculate_merkle_root()
                self.chain.append(block)
        # Broadcast new block
        try:
            from network.p2p_gossip import p2p_gossip
            p2p_gossip.broadcast_block(block.hash)
        except:
            pass

        for tx in block.transactions:
            if not tx.is_system and tx.sender != "EverestKush_Genesis" and tx.sender != SYSTEM_ADDRESS:
                self.spent_outputs.add(tx.calculate_hash())
                self._apply_transaction_to_balances(tx)

        self.pending_transactions = storage.load_pending()
        print(f"[OK] EverestKush Chain loaded: {len(self.chain)} blocks, {len(self.pending_transactions)} pending TXs, Difficulty: {self.difficulty}")

    def _init_balance_db(self):
        conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS balances (
                address TEXT PRIMARY KEY,
                balance REAL NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_balances_address ON balances(address)")
        conn.commit()
        conn.close()

    def _update_balance(self, address, amount):
        if not address or address == "EverestKush_Genesis":
            return
        try:
            conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO balances (address, balance)
                VALUES (?, ?)
                ON CONFLICT(address) DO UPDATE SET
                    balance = balance + excluded.balance,
                    updated_at = CURRENT_TIMESTAMP
            """, (address, amount))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Balance update error: {e}")

    def _apply_transaction_to_balances(self, tx):
        if tx.is_system or tx.sender == "EverestKush_Genesis":
            self._update_balance(tx.recipient, tx.amount)
        else:
            self._update_balance(tx.sender, - (tx.amount + tx.fee))
            self._update_balance(tx.recipient, tx.amount)

    def get_median_time_past(self, block_index=None):
        if block_index is None:
            block_index = len(self.chain) - 1
        start = max(0, block_index - 10)
        timestamps = []
        for i in range(start, block_index + 1):
            if i < len(self.chain):
                timestamps.append(self.chain[i].timestamp)
        if not timestamps:
            return time.time()
        timestamps.sort()
        return timestamps[len(timestamps) // 2]

    def validate_timestamp(self, block_timestamp, prev_block_index=None):
        mtp = self.get_median_time_past(prev_block_index)
        if block_timestamp <= mtp:
            return False
        current_time = time.time()
        if block_timestamp > current_time + 7200:
            return False
        return True

    def get_transaction_weight(self, tx):
        tx_json = json.dumps(tx.to_dict())
        size = len(tx_json.encode())
        base_size = size // 2
        weight = base_size * 3 + size
        return max(weight, 100)

    def _genesis(self) -> EKUSHBlock:
        return EKUSHBlock(0, [], "0" * 64, "EverestKush_Genesis", 1)

    def add_transaction(self, transaction: EKUSHTransaction) -> bool:
        if not transaction.verify():
            return False

        tx_hash = transaction.calculate_hash()

        if not transaction.is_system and transaction.sender != "EverestKush_Genesis" and transaction.sender != SYSTEM_ADDRESS:
            if tx_hash in self.spent_outputs:
                return False
            for pending_tx in self.pending_transactions:
                if pending_tx.sender == transaction.sender and pending_tx.amount == transaction.amount:
                    return False

        # Dust limit check
        if transaction.is_dust():
            print(f"[WARN] Dust transaction rejected: {transaction.amount} below limit")
            return False

        if self.get_balance(transaction.sender) < transaction.amount + transaction.fee:
            return False

        if len(self.pending_transactions) >= self.MAX_MEMPOOL_SIZE:
            self.pending_transactions.sort(key=lambda x: x.fee)
            removed = self.pending_transactions.pop(0)

        self.pending_transactions.append(transaction)
        storage.save_pending(transaction)
        return True

    def add_block(self, validator: str) -> Optional[EKUSHBlock]:
        if not self.pending_transactions and False:  # Allow empty blocks for rewards
            return None

        self.pending_transactions.sort(key=lambda tx: tx.fee, reverse=True)

        total_weight = sum(self.get_transaction_weight(tx) for tx in self.pending_transactions)
        if total_weight > self.MAX_BLOCK_WEIGHT:
            self.pending_transactions.sort(key=lambda tx: tx.fee)
            while total_weight > self.MAX_BLOCK_WEIGHT and self.pending_transactions:
                removed = self.pending_transactions.pop(0)
                total_weight = sum(self.get_transaction_weight(tx) for tx in self.pending_transactions)
            self.pending_transactions.sort(key=lambda tx: tx.fee, reverse=True)

        if not self.validate_timestamp(time.time(), len(self.chain) - 1):
            return None

        self.difficulty = self.difficulty_adjuster.calculate_new_difficulty(self, self.difficulty)

        block_reward = self.difficulty_adjuster.get_block_reward(len(self.chain))
        if block_reward > 0:
            reward_tx = EKUSHTransaction(
                sender=SYSTEM_ADDRESS,
                recipient=validator,
                amount=block_reward,
                fee=0,
                replaceable=False
            )
            reward_tx.is_system = True
            reward_tx.coinbase = True
            reward_tx.mined_at_block = len(self.chain)
            reward_tx.signature = b"system_reward"
            self.pending_transactions.insert(0, reward_tx)
        # Record mining reward in database
        try:
            import sqlite3
            conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
            conn.execute("INSERT OR IGNORE INTO mining_rewards (block_height, validator_address, reward_amount, created_at) VALUES (?, ?, ?, ?)", (len(self.chain), validator, block_reward, int(time.time())))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[WARN] Failed to record mining reward: {e}")

        block = EKUSHBlock(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.chain[-1].hash,
            validator=validator,
            difficulty=self.difficulty
        )
        block.timestamp = int(time.time())
        block.merkle_root = block.calculate_merkle_root()
        block.hash = block.calculate_hash()

        if not block.verify_transactions():
            return None

        verify_checkpoint(block.index, block.hash)
        

        # Check for reorganization
        if len(self.chain) > 0 and block.previous_hash != self.chain[-1].hash:
            print(f"[REORG] Potential reorg detected at height {block.index}")
            from core.reorg import DeepReorgManager
            reorg_mgr = DeepReorgManager()
            result = reorg_mgr.detect_and_recover(block.hash, block.index)
            if result.get("reorg"):
                print(f"[REORG] Reorg completed: disconnected {result.get('disconnected')}, connected {result.get('connected')}")
                # Reload chain after reorg
                time.sleep(0.5)
                return self.add_block(validator)
            else:
                print(f"[ERROR] Reorg rejected: {result.get('error', 'unknown')}")
                return None

        self.chain.append(block)
        # Broadcast new block
        try:
            from network.p2p_gossip import p2p_gossip
            p2p_gossip.broadcast_block(block.hash)
        except:
            pass
        storage.save_block(block)
        storage.clear_pending()

        for tx in block.transactions:
            if not tx.is_system and tx.sender != "EverestKush_Genesis" and tx.sender != SYSTEM_ADDRESS:
                self.spent_outputs.add(tx.calculate_hash())
                self._apply_transaction_to_balances(tx)

        self.pending_transactions = []
        print(f"[MINER] Block #{block.index} mined | Merkle root: {block.merkle_root[:16]}...")
        return block

    def is_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if current.previous_hash != previous.hash:
                return False
        return True

    def get_balance(self, address: str) -> float:
        if not address or address == "EverestKush_Genesis":
            return 0.0

        try:
            conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM balances WHERE address = ?", (address,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else 0.0
        except Exception as e:
            balance = 0
            for block in self.chain:
                for tx in block.transactions:
                    if tx.recipient == address:
                        if hasattr(tx, "coinbase") and tx.coinbase:
                            if len(self.chain) - tx.mined_at_block >= self.COINBASE_MATURITY:
                                balance += tx.amount
                        else:
                            balance += tx.amount
                    if tx.sender == address:
                        balance -= (tx.amount + tx.fee)
            return balance

    def get_latest_block(self) -> EKUSHBlock:
        return self.chain[-1]

    def get_stats(self):
        return storage.get_chain_stats()

    def get_miner_reward(self, block_height):
        return self.difficulty_adjuster.get_block_reward(block_height)

    def get_supply_info(self):
        return self.difficulty_adjuster.get_supply_info(self)

    def is_double_spend(self, tx_hash):
        return tx_hash in self.spent_outputs

    def get_utxo_stats(self):
        return {
            "total_spent_transactions": len(self.spent_outputs),
            "pending_transactions": len(self.pending_transactions),
            "total_blocks": len(self.chain),
            "utxo_set_size": len(self.utxo_set)
        }

    def get_chainstate_stats(self):
        try:
            conn = sqlite3.connect(os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db'), timeout=30)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM balances")
            total_addresses = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(balance) FROM balances")
            total_balance = cursor.fetchone()[0] or 0
            conn.close()
            return {
                "total_addresses": total_addresses,
                "total_balance": total_balance,
                "type": "UTXO_chainstate",
                "lookup_complexity": "O(1)"
            }
        except Exception as e:
            return {"error": str(e)}

    # ========== CONSENSUS & VALIDATION METHODS ==========

    def calculate_chain_work(self):
        """Calculate total cumulative work of the chain (Bitcoin standard)"""
        total_work = 0
        for block in self.chain:
            total_work += block.difficulty
        return total_work

    def get_fork_info(self):
        """Get fork information"""
        blocks_at_height = {}
        for block in self.chain:
            if block.index not in blocks_at_height:
                blocks_at_height[block.index] = []
            blocks_at_height[block.index].append(block)
        
        forks = []
        for height, blocks in blocks_at_height.items():
            if len(blocks) > 1:
                forks.append({
                    "height": height,
                    "blocks": [b.hash[:16] for b in blocks],
                    "count": len(blocks)
                })
        return {
            "has_forks": len(forks) > 0,
            "forks": forks,
            "current_chain_length": len(self.chain),
            "current_work": self.calculate_chain_work()
        }

    def resolve_fork(self, chain_a, chain_b):
        """Resolve fork by choosing chain with more cumulative work"""
        work_a = chain_a.calculate_chain_work()
        work_b = chain_b.calculate_chain_work()
        
        if work_a > work_b:
            return chain_a
        elif work_b > work_a:
            return chain_b
        else:
            return chain_a if len(chain_a.chain) >= len(chain_b.chain) else chain_b

    def validate_coinbase_transaction(self, tx):
        """Enforce Bitcoin standard coinbase transaction format"""
        if not tx.is_system and not tx.coinbase:
            return True
        
        if tx.sender != SYSTEM_ADDRESS:
            print(f"[WARN] Invalid coinbase: sender must be system address")
            return False
        
        if tx.amount <= 0:
            print(f"[WARN] Invalid coinbase: reward must be positive")
            return False
        
        if tx.fee != 0:
            print(f"[WARN] Invalid coinbase: fee must be 0")
            return False
        
        return True

    def __repr__(self):
        return f"EKUSHChain | Blocks: {len(self.chain)} | Pending: {len(self.pending_transactions)} | Difficulty: {self.difficulty} | Spent: {len(self.spent_outputs)}"


def save_chain_to_db(chain):
    for block in chain.chain:
        storage.save_block(block)
    for tx in chain.pending_transactions:
        storage.save_pending(tx)
    return True

def load_chain_from_db():
    from core.block import EKUSHChain, EKUSHBlock

    if not storage.chain_exists():
        return None

    blocks_data = storage.load_chain()
    if not blocks_data:
        return None

    chain = EKUSHChain.__new__(EKUSHChain)
    chain.chain = []
    chain.pending_transactions = storage.load_pending()
    chain.difficulty = 1
    chain.MAX_MEMPOOL_SIZE = 10000
    chain.MAX_BLOCK_WEIGHT = 4000000
    chain.MAX_BLOCK_SIZE = 1000000
    chain.COINBASE_MATURITY = 100
    chain.difficulty_adjuster = DifficultyAdjustment()
    chain.utxo_set = {}
    chain.spent_outputs = set()

    chain._init_balance_db()

    for block_data in blocks_data:
        transactions = block_data["transactions"]
        block = EKUSHBlock(
            index=block_data["index"],
            transactions=transactions,
            previous_hash=block_data["previous_hash"],
            validator=block_data["validator"],
            difficulty=block_data.get("difficulty", 1)
        )
        block.timestamp = block_data["timestamp"]
        block.nonce = block_data["nonce"]
        block.hash = block_data["hash"]
        block.merkle_root = block.calculate_merkle_root()
        chain.chain.append(block)
        chain.difficulty = block.difficulty

        for tx in block.transactions:
            if not tx.is_system and tx.sender != "EverestKush_Genesis" and tx.sender != SYSTEM_ADDRESS:
                chain.spent_outputs.add(tx.calculate_hash())
            chain._apply_transaction_to_balances(tx)

    return chain
