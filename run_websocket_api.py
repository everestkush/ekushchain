#!/usr/bin/env python3
"""
WebSocket API Server - Separate process for WebSocket support
"""
import sys
import os
import signal

sys.path.insert(0, '/home/kushal/everestkush')

def signal_handler(sig, frame):
    print("\n[STOP] Shutting down WebSocket API...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

from api import app, socketio

if __name__ == '__main__':
    print("=" * 60)
    print("EverestKush WebSocket API Server")
    print("=" * 60)
    print(f"   HTTP API: http://localhost:5001")
    print(f"   WebSocket: ws://localhost:5001/socket.io")
    print("   Press Ctrl+C to stop")
    print("=" * 60)
    
    # Run on different port to avoid conflict
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,  # Different port for WebSocket
        debug=False,
        allow_unsafe_werkzeug=True
    )
