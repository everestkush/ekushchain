"""Advanced rate limiting with IP-based + global limits"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

# Configure rate limits based on endpoint sensitivity
RATE_LIMITS = {
    'public': "100 per minute",      # Health, stats, metrics
    'wallet': "20 per minute",       # Wallet operations
    'transaction': "10 per minute",  # Sending transactions
    'admin': "5 per minute",         # Admin operations
    'regtest': "50 per minute"       # Regtest (if enabled)
}

def get_rate_limit(endpoint_type):
    return RATE_LIMITS.get(endpoint_type, "50 per minute")

# Create limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute", "2000 per hour"],
    storage_uri="memory://"
)

def init_limiter(app):
    limiter.init_app(app)
    print("[LOCKED] Rate limiter initialized")
    return limiter
