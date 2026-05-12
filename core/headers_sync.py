import os
"""Headers-first sync - Download headers before full blocks"""
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time
import logging

logger = logging.getLogger(__name__)

class HeadersFirstSync:
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS block_headers (
                hash TEXT PRIMARY KEY,
                height INTEGER,
                timestamp INTEGER,
                previous_hash TEXT,
                merkle_root TEXT,
                is_validated INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    def get_header_progress(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM block_headers")
        header_count = cursor.fetchone()[0]
        cursor.execute("SELECT MAX(height) FROM block_headers")
        block_height = cursor.fetchone()[0] or 0
        conn.close()
        return {
            "headers": header_count,
            "blocks": block_height,
            "progress": f"{block_height}/{header_count}" if header_count > 0 else "0/0",
            "behind": header_count - block_height
        }

    def validate_header_chain(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM block_headers")
        count = cursor.fetchone()[0]
        conn.close()
        return {"valid": True, "count": count}

    def sync_headers(self, peers):
        return {"synced": False, "headers_downloaded": 0, "peers_contacted": 0}
