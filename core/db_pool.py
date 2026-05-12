"""
Database connection pool with WAL mode
"""
import sqlite3
import threading
from contextlib import contextmanager

DB_PATH = "/home/kushal/everestkush/ekush_chain.db"

class DatabasePool:
    _local = threading.local()
    _pool_size = 5
    _connections = []
    _lock = threading.Lock()
    
    @classmethod
    def get_connection(cls):
        """Get a connection with WAL enabled"""
        conn = sqlite3.connect(DB_PATH, timeout=60, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn
    
    @classmethod
    def get_thread_connection(cls):
        """Get connection for current thread"""
        if not hasattr(cls._local, 'conn'):
            cls._local.conn = cls.get_connection()
        return cls._local.conn
    
    @classmethod
    def close_all(cls):
        """Close all connections"""
        if hasattr(cls._local, 'conn'):
            cls._local.conn.close()
            del cls._local.conn

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = DatabasePool.get_connection()
    try:
        yield conn
    finally:
        conn.close()

def get_db_cursor():
    """Get cursor from thread-local connection"""
    return DatabasePool.get_thread_connection().cursor()
