import sqlite3
import threading
import os

DB_PATH = os.environ.get('EKUSH_DB_PATH', '/home/kushal/everestkush/ekush_chain.db')
_local = threading.local()

def get_conn():
    if not hasattr(_local, 'conn') or _local.conn is None:
        _local.conn = sqlite3.connect(
            DB_PATH,
            timeout=30,
            check_same_thread=False
        )
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA synchronous=NORMAL")
        _local.conn.execute("PRAGMA busy_timeout=30000")
        _local.conn.execute("PRAGMA cache_size=10000")
        _local.conn.execute("PRAGMA temp_store=MEMORY")
    return _local.conn

def close_conn():
    if hasattr(_local, 'conn') and _local.conn:
        _local.conn.close()
        _local.conn = None
