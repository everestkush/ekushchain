#!/usr/bin/env python3
"""
Simple HTTP server to serve voting frontend on port 8084
"""
import http.server
import socketserver
import os

PORT = 8084
DIRECTORY = "/home/kushal/everestkush/web"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

print("=" * 60)
print("[VOTE] EverestKush Voting Frontend")
print("=" * 60)
print(f"- Voting Dashboard: http://0.0.0.0:{PORT}/voting/index.html")
print(f"- Block Explorer: http://0.0.0.0:8082")
print(f"- API: http://0.0.0.0:5000")
print("")
print("Press Ctrl+C to stop")
print("=" * 60)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
