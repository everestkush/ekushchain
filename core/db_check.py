"""Database integrity check on startup - detect corruption"""
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import sys
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def check_database_integrity(db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), repair=False):
    """Check SQLite database integrity and optionally repair"""
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Run integrity check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        # Run quick check
        cursor.execute("PRAGMA quick_check")
        quick_result = cursor.fetchone()[0]
        
        # Check foreign keys
        cursor.execute("PRAGMA foreign_key_check")
        fk_errors = cursor.fetchall()
        
        conn.close()
        
        if result == "ok" and quick_result == "ok" and not fk_errors:
            logger.info("[OK] Database integrity check passed")
            return True
        else:
            logger.error(f"[ERROR] Database corruption detected: {result}")
            if fk_errors:
                logger.error(f"Foreign key errors: {fk_errors}")
            
            if repair:
                return repair_database(db_path)
            return False
    
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False

def repair_database(db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")):
    """Attempt to repair corrupted database"""
    logger.warning("Attempting database repair...")
    
    backup_path = f"{db_path}.corrupt_backup"
    os.rename(db_path, backup_path)
    logger.info(f"Backed up corrupt DB to {backup_path}")
    
    try:
        # Create new database
        conn = get_conn()
        cursor = conn.cursor()
        
        # Attach old database
        cursor.execute(f"ATTACH DATABASE '{backup_path}' AS old")
        
        # Recreate tables (add your schema here)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blocks (
                block_hash TEXT PRIMARY KEY,
                height INTEGER,
                timestamp INTEGER,
                previous_hash TEXT
            )
        """)
        
        # Copy recoverable data
        cursor.execute("""
            INSERT OR IGNORE INTO blocks 
            SELECT * FROM old.blocks WHERE block_hash IS NOT NULL
        """)
        
        cursor.execute("DETACH DATABASE old")
        conn.commit()
        conn.close()
        
        logger.info("[OK] Database repaired successfully")
        return True
    
    except Exception as e:
        logger.error(f"Repair failed: {e}")
        logger.warning(f"Manual recovery required from {backup_path}")
        return False

def verify_on_startup(db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), required_tables=None):
    """Verify database on node startup"""
    if required_tables is None:
        required_tables = ['blocks', 'utxoset', 'chain_state', 'mempool']
    
    if not check_database_integrity(db_path):
        logger.critical("Database integrity check failed. Node cannot start.")
        sys.exit(1)
    
    # Verify required tables exist
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    missing = [t for t in required_tables if t not in existing_tables]
    if missing:
        logger.critical(f"Missing required tables: {missing}")
        sys.exit(1)
    
    logger.info("Database verification complete - all checks passed")
    return True
