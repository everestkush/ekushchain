import socket
import json
import threading
import time
import sys
from collections import deque

class P2PGossip:
    def __init__(self, host='0.0.0.0', port=8334, seed_nodes=None):
        self.host = host
        self.port = port
        self.seed_nodes = seed_nodes or ['103.74.15.88:8334', '192.168.23.5:8334']
        self.peers = set()
        self.running = False
        self.message_queue = deque()
        self.broadcast_queue = deque()
        self.known_tx = set()
        self.known_blocks = set()

    def _log(self, msg):
        with open('/tmp/p2p_gossip.log', 'a') as f:
            f.write(f"{time.time()} [P2P] {msg}\n")
        sys.stderr.write(f"[P2P] {msg}\n")
        sys.stderr.flush()

    def start(self):
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        self.gossip_thread = threading.Thread(target=self._gossip_loop, daemon=True)
        self.gossip_thread.start()
        self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.broadcast_thread.start()
        self._connect_to_seeds()
        self._log(f"P2P gossip started on port {self.port}")
        return True

    def _run_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(100)
        self._log(f"Server listening on {self.port}")
        while self.running:
            try:
                client, addr = server.accept()
                self._log(f"Client connected from {addr}")
                threading.Thread(target=self._handle_client, args=(client, addr), daemon=True).start()
            except Exception as e:
                self._log(f"Server accept error: {e}")

    def _handle_client(self, client, addr):
        try:
            while self.running:
                data = client.recv(65536)
                if not data:
                    break
                self._log(f"Received data from {addr}: {len(data)} bytes")
                self._process_message(data.decode(), addr)
                client.send(b'OK')
        except Exception as e:
            self._log(f"Client handler error: {e}")
        finally:
            client.close()

    def _process_message(self, msg, addr):
        try:
            data = json.loads(msg)
            msg_type = data.get('type')
            payload = data.get('payload')

            if msg_type == 'tx':
                tx_hash = payload.get('hash')
                if tx_hash not in self.known_tx:
                    self.known_tx.add(tx_hash)
                    self.message_queue.append(data)
                    self._relay_to_peers(data)
                    self._log(f"RECEIVED TX from {addr}: {tx_hash[:16]}")
                else:
                    self._log(f"Duplicate TX ignored: {tx_hash[:16]}")
            elif msg_type == 'block':
                block_hash = payload.get('hash')
                if block_hash not in self.known_blocks:
                    self.known_blocks.add(block_hash)
                    self.message_queue.append(data)
                    self._relay_to_peers(data)
                    self._log(f"RECEIVED BLOCK from {addr}: {block_hash[:16]}")
            elif msg_type == 'getblocks':
                self._send_blocks(client, payload)
            else:
                self._log(f"Unknown message type: {msg_type}")
        except Exception as e:
            self._log(f"Process message error: {e}")

    def _relay_to_peers(self, msg):
        for peer in list(self.peers):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect(peer)
                s.send(json.dumps(msg).encode())
                s.close()
                self._log(f"Relayed to peer: {peer}")
            except Exception as e:
                self._log(f"Failed to relay to {peer}: {e}")

    def _gossip_loop(self):
        while self.running:
            if self.message_queue:
                msg = self.message_queue.popleft()
                self._relay_to_peers(msg)
            time.sleep(0.1)

    def _broadcast_loop(self):
        while self.running:
            if self.broadcast_queue:
                msg = self.broadcast_queue.popleft()
                self._relay_to_peers(msg)
            time.sleep(0.1)

    def _connect_to_seeds(self):
        for seed in self.seed_nodes:
            try:
                host, port = seed.split(':')
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((host, int(port)))
                self.peers.add((host, int(port)))
                s.close()
                self._log(f"Connected to seed: {seed}")
            except Exception as e:
                self._log(f"Failed to connect to seed {seed}: {e}")

    def broadcast_transaction(self, tx_hash):
        msg = json.dumps({
            'type': 'tx',
            'payload': {'hash': tx_hash, 'timestamp': int(time.time())}
        })
        self.broadcast_queue.append(msg)
        self._log(f"Broadcasting tx: {tx_hash[:16]}")

    def broadcast_block(self, block_hash):
        msg = json.dumps({
            'type': 'block',
            'payload': {'hash': block_hash, 'timestamp': int(time.time())}
        })
        self.broadcast_queue.append(msg)
        self._log(f"Broadcasting block: {block_hash[:16]}")

    def stop(self):
        self.running = False

p2p_gossip = P2PGossip()
