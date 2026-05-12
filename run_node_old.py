#!/usr/bin/env python3
import sys
import os

# Initialize database first
sys.path.insert(0, "/home/kushal/everestkush")
from core.db_init import ensure_initialized
ensure_initialized()

#!/usr/bin/env python3
import sys
import os
import signal

sys.path.insert(0, '/home/kushal/everestkush')

def signal_handler(sig, frame):
    print("\n[STOP] Shutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start P2P server
try:
    from network.p2p_server import start_p2p, get_p2p
    print("Starting P2P server...")
    p2p_server = start_p2p()
    if p2p_server:
        print(f"[OK] P2P server running on port 8333")
    else:
        print("[ERROR] Failed to start P2P server")
except Exception as e:
    print(f"[WARN] P2P not started: {e}")

# Import and run API with WebSocket support
from api import app
try:
    from network.sync import start_auto_sync
except ImportError:
    start_auto_sync = None
# Start election auto-close scheduler
from election_scheduler import start_scheduler
scheduler_thread = start_scheduler()
import gunicorn.app.base

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        # Map our options to Gunicorn config keys
        config_map = {
            'bind': 'bind',
            'workers': 'workers',
            'worker_class': 'worker_class',
            'threads': 'threads',
            'worker_connections': 'worker_connections',
            'timeout': 'timeout',
            'keepalive': 'keepalive',
            'max_requests': 'max_requests',
            'max_requests_jitter': 'max_requests_jitter',
            'graceful_timeout': 'graceful_timeout',
            'reload': 'reload',
            'accesslog': 'accesslog',
            'errorlog': 'errorlog',
            'loglevel': 'loglevel',
        }
        
        for key, value in self.options.items():
            if key in config_map:
                self.cfg.set(config_map[key], value)
            elif key not in ['debug']:  # Skip debug - not a Gunicorn setting
                print(f"[WARN] Unknown config option: {key}")

    def load(self):
        return self.application

if __name__ == '__main__':
    options = {
        'bind': '0.0.0.0:5000',
        'worker_class': 'gevent',
        'workers': 1,
        'threads': 1,
        'worker_connections': 1000,
        'timeout': 30,
        'keepalive': 5,
        'max_requests': 10000,
        'max_requests_jitter': 1000,
        'graceful_timeout': 10,
        'reload': False,
        'accesslog': '-',
        'errorlog': '-',
        'loglevel': 'info',
        # 'debug' removed - not a valid Gunicorn setting
    }
    print("=" * 60)
    print("Starting EverestKush API with WebSocket support")
    print("=" * 60)
    print(f"   HTTP API: http://localhost:5000")
    print(f"   WebSocket: ws://localhost:5000/socket.io")
    print(f"   Worker Class: {options['worker_class']}")
    print(f"   Workers: {options['workers']}")
    print("=" * 60)
    StandaloneApplication(app, options).run()
import time


import time


# ========== SINGLE MINING THREAD ==========
import threading
import time
import sqlite3
from core.block import EKUSHChain

def mine_blocks():
    """Simple mining worker"""
    print("[MINER] MINER: Starting...")
    time.sleep(10)  # Wait for API to start
    
    while True:
        try:
            # Get validator
            conn = sqlite3.connect('ekush_chain.db', timeout=60)
            row = conn.execute("SELECT address FROM validators WHERE status='active' LIMIT 1").fetchone()
            conn.close()
            
            if not row:
                time.sleep(5)
                continue
                
            validator = row[0]
            
            # Create chain and mine
            bc = EKUSHChain()
            block = bc.add_block(validator)
            
            if block:
                print(f"[MINER] MINER: Block #{block.index} MINED!")
            else:
                pass  # No transactions, just wait
                
        except Exception as e:
            print(f"[MINER] MINER ERROR: {e}")
            
        time.sleep(3)

miner_thread = threading.Thread(target=mine_blocks, daemon=True)
miner_thread.start()
print("[MINER] MINER THREAD STARTED")
