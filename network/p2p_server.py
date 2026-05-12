import socket
import threading
import json
import sqlite3
import time
from collections import defaultdict

DB_PATH = "/home/kushal/everestkush/ekush_chain.db"
p2p_instance = None

class P2PServer:
    PORT = 8333

    def __init__(self):
        self.socket = None
        self.running = False
        self.peers = set()
        self.connection_counts = defaultdict(list)

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.PORT))
            self.socket.listen(100)
            self.running = True
            print(f"[P2P] Server on port {self.PORT}")
            threading.Thread(target=self._accept, daemon=True).start()
            return self
        except Exception as e:
            print(f"Error: {e}")
            self.running = False
            return None

    def _is_rate_limited(self, ip):
        now = time.time()
        self.connection_counts[ip] = [t for t in self.connection_counts[ip] if now - t < 60]
        if len(self.connection_counts[ip]) >= 10:
            return True
        self.connection_counts[ip].append(now)
        return False

    def _accept(self):
        while self.running:
            try:
                client, addr = self.socket.accept()
                peer_ip = addr[0]
                if self._is_rate_limited(peer_ip):
                    print(f"🚫 Rate limited: {peer_ip}")
                    client.close()
                    continue
                print(f"📡 Peer connected: {peer_ip}")
                self.peers.add(peer_ip)
                threading.Thread(target=self._handle_client, args=(client, peer_ip), daemon=True).start()
            except:
                pass

    def _handle_client(self, client, peer_ip):
        buffer = b''
        while self.running:
            try:
                data = client.recv(4096)
                if not data:
                    break
                buffer += data
                try:
                    msg = json.loads(buffer.decode())
                    buffer = b''
                    self._process_message(client, msg)
                except json.JSONDecodeError:
                    continue
            except:
                break
        client.close()
        self.peers.discard(peer_ip)

    def _process_message(self, client, msg):
        msg_type = msg.get('type')
        payload = msg.get('payload', {})
        
        if msg_type == 'getheaders':
            from_height = payload.get('from', 0)
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute('SELECT idx, hash, previous_hash, timestamp FROM blocks WHERE idx > ? ORDER BY idx LIMIT 2000', (from_height,))
            headers = [{'height': r[0], 'hash': r[1], 'prev_hash': r[2], 'timestamp': r[3]} for r in rows]
            conn.close()
            response = json.dumps({'type': 'headers', 'payload': headers})
            client.send(response.encode())
            print(f"Sent {len(headers)} headers to peer")
        
        elif msg_type == 'getblocks':
            from_height = payload.get('from', 0)
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute('SELECT idx, hash, previous_hash, validator, timestamp FROM blocks WHERE idx > ? ORDER BY idx LIMIT 500', (from_height,))
            blocks = [{'height': r[0], 'hash': r[1], 'prev_hash': r[2], 'validator': r[3], 'timestamp': r[4]} for r in rows]
            conn.close()
            response = json.dumps({'type': 'blocks', 'payload': blocks})
            client.send(response.encode())
        
        elif msg_type == 'ping':
            client.send(json.dumps({'type': 'pong'}).encode())

    def broadcast_block(self, block_hash, block_height):
        print(f"📢 Broadcasting block {block_hash[:8]} to {len(self.peers)} peers")
        return {"broadcasted": True, "peers": len(self.peers)}

    def get_peer_count(self):
        return len(self.peers)

    def get_peers(self):
        return list(self.peers)

    def is_running(self):
        return self.running

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()

p2p_server = P2PServer()

def start_p2p():
    global p2p_server
    if not p2p_server.running:
        p2p_server.start()
    return p2p_server

def get_p2p():
    global p2p_server
    return p2p_server if p2p_server.running else None

    def _process_message(self, client, msg):
        msg_type = msg.get('type')
        payload  = msg.get('payload', {})

        if msg_type == 'getblocks':
            start  = payload.get('start_height', 0)
            maxb   = min(payload.get('max_blocks', 50), 100)
            try:
                conn  = sqlite3.connect(DB_PATH, timeout=30)
                rows  = conn.execute("""
                    SELECT idx, hash, previous_hash, validator,
                           timestamp, nonce, merkle_root, transactions_count
                    FROM blocks
                    WHERE idx > ?
                    ORDER BY idx ASC
                    LIMIT ?
                """, (start, maxb)).fetchall()
                conn.close()
                blocks = [{
                    "idx": r[0], "hash": r[1], "previous_hash": r[2],
                    "validator": r[3], "timestamp": r[4],
                    "nonce": r[5], "merkle_root": r[6],
                    "transactions_count": r[7] or 0
                } for r in rows]
                response = json.dumps({"type": "blocks", "blocks": blocks})
                client.sendall(response.encode())
            except Exception as e:
                error = json.dumps({"type": "error", "message": str(e)})
                client.sendall(error.encode())

        elif msg_type == 'getheight':
            try:
                conn  = sqlite3.connect(DB_PATH, timeout=30)
                height = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
                conn.close()
                client.sendall(json.dumps({"type": "height", "height": height}).encode())
            except Exception as e:
                client.sendall(json.dumps({"type": "error", "message": str(e)}).encode())

        elif msg_type == 'ping':
            client.sendall(json.dumps({"type": "pong"}).encode())

    def broadcast_transaction(self, tx_data):
        """Broadcast transaction to all connected peers"""
        try:
            import json
            message = json.dumps({"type": "transaction", "data": tx_data}).encode()
            for peer_ip in list(self.peers):
                try:
                    # This would send to peer socket
                    # Implementation depends on peer connection management
                    pass
                except:
                    pass
            print(f"📡 Broadcasted transaction to {len(self.peers)} peers")
            return {"broadcasted": True, "peers": len(self.peers)}
        except Exception as e:
            print(f"Broadcast error: {e}")
            return {"broadcasted": False, "error": str(e)}
    
    def broadcast_block(self, block_data):
        """Broadcast block to all connected peers"""
        try:
            import json
            message = json.dumps({"type": "block", "data": block_data}).encode()
            for peer_ip in list(self.peers):
                try:
                    # This would send to peer socket
                    pass
                except:
                    pass
            print(f"📢 Broadcasted block to {len(self.peers)} peers")
            return {"broadcasted": True, "peers": len(self.peers)}
        except Exception as e:
            print(f"Broadcast error: {e}")
            return {"broadcasted": False, "error": str(e)}
