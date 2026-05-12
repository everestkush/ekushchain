#!/usr/bin/env python3
import sys
import os
import signal

sys.path.insert(0, '/home/kushal/everestkush')

# Initialize database first
from core.db_init import ensure_initialized
ensure_initialized()

def signal_handler(sig, frame):
    print("\n[STOP] Shutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start P2P gossip
from network.p2p_gossip import p2p_gossip
p2p_gossip.start()
print("P2P gossip started")

# Start P2P server
try:
    from network.p2p_server import start_p2p, get_p2p
    print("Starting P2P server...")
    p2p_server = start_p2p()
    if p2p_server:
        print("[OK] P2P server running on port 8333")
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

# Start P2P gossip for transaction/block broadcasting
