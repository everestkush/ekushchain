#!/usr/bin/env python3
"""
Unified server for Voting Frontend + API Proxy (no CORS issues)
Serves on port 8084
"""
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

PORT = 8084
DIRECTORY = "/home/kushal/everestkush/voting"
API_URL = "http://localhost:5000"

class ProxyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        # Handle API proxy requests
        if self.path.startswith('/api/'):
            self.proxy_request('GET')
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_request('POST')
        else:
            super().do_POST()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def proxy_request(self, method):
        try:
            # Convert /api/elections to /elections
            api_path = self.path.replace('/api', '')
            
            # Read body for POST
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Build request
            url = f"{API_URL}{api_path}"
            req = urllib.request.Request(url, data=body, method=method)
            
            # Copy content type header
            if 'Content-Type' in self.headers:
                req.add_header('Content-Type', self.headers['Content-Type'])
            
            # Make request to API
            with urllib.request.urlopen(req, timeout=30) as response:
                self.send_response(response.status)
                self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
                self.end_headers()
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def log_message(self, format, *args):
        # Suppress logging for cleaner output
        pass

# Update the HTML to use the proxy
html_path = os.path.join(DIRECTORY, 'voting', 'index.html')
if os.path.exists(html_path):
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    # Replace API_URL with proxy URL
    html_content = html_content.replace("'http://localhost:5000'", "''")
    html_content = html_content.replace("'http://103.74.15.88:5000'", "''")
    html_content = html_content.replace("const API_URL = window.location.hostname === 'localhost'", 
                                        "const API_URL = ''")
    html_content = html_content.replace("? 'http://localhost:5000' : 'http://103.74.15.88:5000'", 
                                        "? '/api' : '/api'")
    
    # Simple fix: use relative path
    html_content = html_content.replace("const API_URL =", "const API_URL = '/api'; //")
    
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    print("[OK] Updated HTML to use proxy")

print("=" * 60)
print("[VOTE] EverestKush Voting Platform (No CORS Issues)")
print("=" * 60)
print(f"- Voting Dashboard: http://0.0.0.0:{PORT}/voting/index.html")
print(f"- API Proxy: /api/* -> {API_URL}")
print("")
print("Press Ctrl+C to stop")
print("=" * 60)

HTTPServer(("0.0.0.0", PORT), ProxyHandler).serve_forever()
