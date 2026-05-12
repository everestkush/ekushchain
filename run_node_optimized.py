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
    from network.p2p_server import start_p2p
    print("Starting P2P server...")
    p2p_server = start_p2p()
    if p2p_server:
        print(f"[OK] P2P server running on port 8333")
except Exception as e:
    print(f"[WARN] P2P not started: {e}")

# Import and run API
from api_postgres import app
import gunicorn.app.base

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

if __name__ == '__main__':
    options = {
        'bind': '0.0.0.0:5000',
        'workers': 16,
        'threads': 32,
        'worker_connections': 2000,
        'timeout': 30,
        'keepalive': 5,
        'max_requests': 10000,
        'max_requests_jitter': 1000,
        'graceful_timeout': 10,
        'worker_class': 'gthread',
        'preload_app': True,
    }
    print("=" * 50)
    print("EVERESTKUSH OPTIMIZED SERVER")
    print(f"Workers: {options['workers']}, Threads: {options['threads']}")
    print(f"Database: PostgreSQL + Redis")
    print("=" * 50)
    StandaloneApplication(app, options).run()
