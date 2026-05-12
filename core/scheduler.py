import threading
import time
import requests

class BlockScheduler:
    def __init__(self, chain, node, registry, storage_funcs):
        self.chain = chain
        self.node = node
        self.registry = registry
        self.save_chain = storage_funcs['save']
        self.clear_pending = storage_funcs['clear']
        self.running = False
        self.block_time = 3  # seconds
        self.thread = None
        self.my_validator_address = None

    def set_validator(self, address):
        self.my_validator_address = address
        print(f"Scheduler: I am validator {address[:16]}...")

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"Block scheduler started -- producing every {self.block_time}s")

    def stop(self):
        self.running = False
        print("Block scheduler stopped")

    def _run(self):
        while self.running:
            try:
                self._try_produce_block()
            except Exception as e:
                print(f"Scheduler error: {e}")
            time.sleep(self.block_time)

    def _try_produce_block(self):
        if not self.my_validator_address:
            return

        if not self.chain.pending_transactions:
            return

        # REMOVED: Turn check - mine ANY pending transaction immediately
        # expected = self.registry.get_next_validator(len(self.chain.chain))
        # if expected != self.my_validator_address:
        #     return

        # Produce the block immediately
        print(f"Producing block #{len(self.chain.chain)} as {self.my_validator_address[:16]}...")
        block = self.chain.add_block(self.my_validator_address)
        if block:
            self.save_chain(self.chain)
            self.clear_pending()
            self.registry.record_block(self.my_validator_address)
            self.node.broadcast_block(block)
            print(f"Block #{block.index} produced and broadcast -- {len(block.transactions)} TXs")
