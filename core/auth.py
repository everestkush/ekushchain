from functools import wraps
from flask import request, jsonify
import os

API_KEY = os.getenv("API_KEY", "CHANGE_ME")

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "Missing API key", "message": "Use X-API-Key header"}), 401
        if api_key != API_KEY:
            return jsonify({"error": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated
