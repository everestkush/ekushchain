import os
import json
from rocksdict import Rdict, AccessType

ROCKSDB_PATH = os.environ.get('EKUSH_ROCKSDB_PATH', '/home/kushal/everestkush/rocksdb_data')
IS_MINER = os.environ.get('EVERESTKUSH_MODE', 'api') == 'miner'

class RocksDBStorage:
    def __init__(self):
        # Use read-write for miner, read-only for API
        access_type = AccessType.read_write() if IS_MINER else AccessType.read_only()
        self.blocks_db = Rdict(f"{ROCKSDB_PATH}/blocks", access_type=access_type)
        self.txs_db = Rdict(f"{ROCKSDB_PATH}/transactions", access_type=access_type)
        self.utxos_db = Rdict(f"{ROCKSDB_PATH}/utxos", access_type=access_type)
        self.chainstate_db = Rdict(f"{ROCKSDB_PATH}/chainstate", access_type=access_type)
        self.metadata_db = Rdict(f"{ROCKSDB_PATH}/metadata", access_type=access_type)

    def save_block(self, block):
        if not IS_MINER:
            raise Exception("Only miner can write blocks")
        key = f"block:{block.index}".encode()
        value = json.dumps({
            'idx': block.index,
            'hash': block.hash,
            'previous_hash': block.previous_hash,
            'validator': block.validator,
            'timestamp': block.timestamp,
            'nonce': block.nonce,
            'merkle_root': block.merkle_root,
            'transactions_count': len(block.transactions)
        }).encode()
        self.blocks_db[key] = value
        self.chainstate_db[b'best_height'] = str(block.index).encode()
        self.chainstate_db[b'best_hash'] = block.hash.encode()

    def get_block(self, height):
        key = f"block:{height}".encode()
        value = self.blocks_db.get(key)
        return json.loads(value.decode()) if value else None

    def get_latest_height(self):
        value = self.chainstate_db.get(b'best_height')
        return int(value.decode()) if value else 0

    def save_transaction(self, tx):
        if not IS_MINER:
            raise Exception("Only miner can write transactions")
        key = f"tx:{tx.txid}".encode()
        value = json.dumps({
            'tx_hash': tx.txid,
            'sender': tx.sender,
            'recipient': tx.recipient,
            'amount': tx.amount,
            'fee': tx.fee,
            'timestamp': tx.timestamp,
            'signature': tx.signature.hex() if tx.signature else None,
            'public_key': tx.public_key
        }).encode()
        self.txs_db[key] = value

    def get_transaction(self, txid):
        key = f"tx:{txid}".encode()
        value = self.txs_db.get(key)
        return json.loads(value.decode()) if value else None

    def save_utxo(self, outpoint, address, amount, script_pubkey="", block_height=None):
        if not IS_MINER:
            raise Exception("Only miner can write UTXOs")
        key = f"utxo:{outpoint}".encode()
        value = json.dumps({
            'outpoint': outpoint,
            'address': address,
            'amount': amount,
            'script_pubkey': script_pubkey,
            'block_height': block_height,
            'is_spent': 0,
            'created_at': int(__import__('time').time())
        }).encode()
        self.utxos_db[key] = value

    def spend_utxo(self, outpoint):
        if not IS_MINER:
            raise Exception("Only miner can spend UTXOs")
        key = f"utxo:{outpoint}".encode()
        value = self.utxos_db.get(key)
        if value:
            utxo = json.loads(value.decode())
            utxo['is_spent'] = 1
            self.utxos_db[key] = json.dumps(utxo).encode()
            return True
        return False

    def get_utxos(self, address):
        utxos = []
        for key, value in self.utxos_db.items():
            utxo = json.loads(value.decode())
            if utxo['address'] == address and not utxo.get('is_spent', 0):
                utxos.append(utxo)
        return utxos

    def close(self):
        self.blocks_db.close()
        self.txs_db.close()
        self.utxos_db.close()
        self.chainstate_db.close()
        self.metadata_db.close()

rocksdb_storage = RocksDBStorage()
