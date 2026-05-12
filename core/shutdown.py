import os
"""Graceful shutdown - flush mempool, close DB cleanly"""
import signal
import sys
import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import json
import time
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class GracefulShutdown:
    def __init__(self, db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), mempool=None, p2p_server=None, api_server=None):
        self.db_path = db_path
        self.mempool = mempool or []
        self.p2p_server = p2p_server
        self.api_server = api_server
        self.shutdown_in_progress = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        if self.shutdown_in_progress:
            logger.warning("Forced shutdown...")
            sys.exit(1)
        
        logger.info(f"Received signal {signum}, starting graceful shutdown...")
        self.shutdown_in_progress = True
        self._shutdown()
    
    def _shutdown(self):
        """Perform graceful shutdown"""
        logger.info("Step 1/4: Saving mempool...")
        self._save_mempool()
        
        logger.info("Step 2/4: Flushing database...")
        self._flush_database()
        
        logger.info("Step 3/4: Stopping P2P server...")
        self._stop_p2p()
        
        logger.info("Step 4/4: Stopping API server...")
        self._stop_api()
        
        # Write shutdown marker
        with open("shutdown_clean", 'w') as f:
            f.write(json.dumps({
                'timestamp': datetime.now().isoformat(),
                'status': 'clean'
            }))
        
        logger.info("[OK] Graceful shutdown complete")
        sys.exit(0)
    
    def _save_mempool(self):
        """Save mempool to disk"""
        if self.mempool:
            mempool_file = Path("mempool_backup.json")
            with open(mempool_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'count': len(self.mempool),
                    'transactions': self.mempool
                }, f, indent=2)
            logger.info(f"Saved {len(self.mempool)} transactions to {mempool_file}")
        else:
            logger.info("Mempool empty, nothing to save")
    
    def _flush_database(self):
        """Flush and checkpoint database"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.execute("PRAGMA optimize")
            conn.close()
            logger.info("Database checkpointed and optimized")
        except Exception as e:
            logger.error(f"Database flush failed: {e}")
    
    def _stop_p2p(self):
        """Stop P2P server gracefully"""
        if self.p2p_server and hasattr(self.p2p_server, 'stop'):
            try:
                self.p2p_server.stop()
                logger.info("P2P server stopped")
            except Exception as e:
                logger.error(f"Error stopping P2P server: {e}")
    
    def _stop_api(self):
        """Stop API server gracefully"""
        if self.api_server:
            try:
                # For Flask with Gunicorn
                if hasattr(self.api_server, 'shutdown'):
                    self.api_server.shutdown()
                logger.info("API server stopped")
            except Exception as e:
                logger.error(f"Error stopping API server: {e}")

def setup_graceful_shutdown(db_path=os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), mempool=None):
    """Convenience function to setup graceful shutdown"""
    return GracefulShutdown(db_path, mempool)

def restore_mempool_if_exists():
    """Restore mempool from backup on startup"""
    mempool_file = Path("mempool_backup.json")
    if mempool_file.exists():
        try:
            with open(mempool_file) as f:
                data = json.load(f)
            logger.info(f"Restored {data['count']} transactions from backup")
            mempool_file.unlink()  # Remove backup after restore
            return data.get('transactions', [])
        except Exception as e:
            logger.error(f"Failed to restore mempool: {e}")
    return []
