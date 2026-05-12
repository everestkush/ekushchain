from flask import request

ALLOWED_ORIGINS = [
    'https://103.74.15.88:8080',
    'http://103.74.15.88:8080',
    'https://localhost:8080',
    'http://localhost:8080'
]

def init_cors(app):
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin and origin in ALLOWED_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key'
        # If origin is NOT allowed, NO CORS header is added
        return response
