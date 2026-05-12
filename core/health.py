import os
"""Health check endpoint with chain tip age alert"""
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time
from datetime import datetime
from flask import jsonify

def check_health(db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), max_tip_age_seconds=3600):
    """Check node health and chain tip age"""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT timestamp, height FROM blocks ORDER BY height DESC LIMIT 1")
        last_block = cursor.fetchone()
        
        conn.close()
        
        if not last_block:
            return {
                'healthy': False,
                'error': 'No blocks found in database',
                'timestamp': datetime.now().isoformat()
            }
        
        last_time, height = last_block
        now = int(time.time())
        tip_age_seconds = now - last_time
        is_healthy = tip_age_seconds < max_tip_age_seconds
        
        status = {
            'healthy': is_healthy,
            'chain_height': height,
            'tip_age_seconds': tip_age_seconds,
            'tip_age_hours': round(tip_age_seconds / 3600, 2),
            'max_allowed_tip_age': max_tip_age_seconds,
            'timestamp': datetime.now().isoformat(),
            'service': 'everestkush-node',
            'version': '1.0'
        }
        
        return status
    
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def create_health_endpoint(app, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")):
    """Add health check endpoint to Flask app"""
    @app.route('/health')
    def health():
        status = check_health(db_path)
        http_status = 200 if status['healthy'] else 503
        return jsonify(status), http_status
    
    @app.route('/health/ready')
    def ready():
        status = check_health(db_path)
        if status['healthy']:
            return jsonify({'ready': True}), 200
        return jsonify({'ready': False}), 503
    
    @app.route('/health/live')
    def live():
        return jsonify({'alive': True}), 200
    
    return app
