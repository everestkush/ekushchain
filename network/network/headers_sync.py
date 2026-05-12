"""Headers-first sync - Download headers before full blocks"""
import sqlite3
import time
import threading
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class HeadersFirstSync:
    """Download and validate headers before full blocks"""
    
    def __init__(self, db_path="ekush_chain.db"):
        self.db_path = db_path
        self.sync_in_progress = False
        self.peer_headers = {}
        self.best_header_hash = None
        self.best_header_height = 0
    
    def download_headers(self, peer_url: str, start_height: int = 0) -> List[Dict]:
        """Download headers from peer"""
        import requests
        try:
            response = requests.get(
                f"{peer_url}/headers?start={start_height}",
                timeout=30
            )
            if response.status_code == 200:
                headers = response.json()
                self._store_headers(headers)
                return headers
        except Exception as e:
            logger.error(f"Failed to download headers: {e}")
        return []
    
    def _store_headers(self, headers: List[Dict]):
        """Store headers in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create headers table if not exists
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
        
        for header in headers:
            cursor.execute('''
                INSERT OR REPLACE INTO block_headers 
                (hash, height, timestamp, previous_hash, merkle_root)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                header.get('hash'),
                header.get('height'),
                header.get('timestamp'),
                header.get('previous_hash'),
                header.get('merkle_root')
            ))
        
        conn.commit()
        conn.close()
    
    def validate_header_chain(self) -> bool:
        """Validate header chain integrity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT hash, height, previous_hash 
            FROM block_headers 
            ORDER BY height ASC
        ''')
        
        headers = cursor.fetchall()
        conn.close()
        
        if len(headers) < 2:
            return True
        
        # Verify chain links
        for i in range(1, len(headers)):
            current = headers[i]
            previous = headers[i-1]
            
            # Check height ordering
            if current[1] != previous[1] + 1:
                return False
            
            # Check previous hash link
            if current[2] != previous[0]:
                return False
        
        logger.info(f"Validated {len(headers)} headers")
        return True
    
    def sync_headers(self, peers: List[str]) -> Dict:
        """Synchronize headers from multiple peers"""
        self.sync_in_progress = True
        result = {
            "synced": False,
            "headers_downloaded": 0,
            "peers_contacted": 0
        }
        
        for peer in peers:
            try:
                headers = self.download_headers(peer)
                if headers:
                    result["headers_downloaded"] = len(headers)
                    result["synced"] = True
                    break
                result["peers_contacted"] += 1
            except:
                continue
        
        if result["synced"]:
            result["valid"] = self.validate_header_chain()
        
        self.sync_in_progress = False
        return result
    
    def get_header_progress(self) -> Dict:
        """Get header synchronization progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM block_headers")
        header_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(height) FROM blocks")
        block_height = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "headers": header_count,
            "blocks": block_height,
            "progress": f"{block_height}/{header_count}" if header_count > 0 else "0/0",
            "behind": header_count - block_height
        }
