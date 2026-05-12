import os
"""
Election Scheduler - Checks block height and closes elections automatically
Runs every 3 seconds (1 block)
"""

import sqlite3
try:
    from core.db import get_conn
except ImportError:
    get_conn = lambda: __import__("sqlite3").connect(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db"), timeout=30)
import time
import threading
import json
from datetime import datetime

DB_PATH = "/home/kushal/everestkush/ekush_chain.db"

class ElectionScheduler:
    def __init__(self):
        self.db_path = DB_PATH
        self.running = True
        self._init_tables()
    
    def _init_tables(self):
        with get_conn() as conn:
            cur = conn.cursor()
            # Add end_block column if not exists
            cur.execute("PRAGMA table_info(elections)")
            columns = [col[1] for col in cur.fetchall()]
            
            if 'end_block' not in columns:
                cur.execute("ALTER TABLE elections ADD COLUMN end_block INTEGER DEFAULT 0")
            if 'start_block' not in columns:
                cur.execute("ALTER TABLE elections ADD COLUMN start_block INTEGER DEFAULT 0")
            if 'result_winner' not in columns:
                cur.execute("ALTER TABLE elections ADD COLUMN result_winner TEXT")
            if 'result_sealed' not in columns:
                cur.execute("ALTER TABLE elections ADD COLUMN result_sealed INTEGER DEFAULT 0")
            if 'op_return_tx' not in columns:
                cur.execute("ALTER TABLE elections ADD COLUMN op_return_tx TEXT")
            
            # Create votes table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS election_votes (
                    vote_id TEXT PRIMARY KEY,
                    election_id TEXT,
                    option_id INTEGER,
                    voter_id TEXT,
                    created_at INTEGER
                )
            """)
            conn.commit()
    
    def get_current_block(self):
        """Get current block height"""
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM blocks")
            return cur.fetchone()[0]
    
    def check_and_close_elections(self):
        """Check for elections that need to be closed"""
        current_block = self.get_current_block()
        
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT election_id, title, end_block, status 
                FROM elections 
                WHERE status = 'active' AND end_block <= ? AND end_block > 0
            """, (current_block,))
            
            to_close = cur.fetchall()
            
            for election_id, title, end_block, status in to_close:
                print(f"[LOCKED] Closing election: {title} (ID: {election_id})")
                self.close_election(election_id)
    
    def close_election(self, election_id):
        """Close election, tally votes, determine winner"""
        with get_conn() as conn:
            cur = conn.cursor()
            
            # Get election info
            cur.execute("SELECT title, candidates FROM elections WHERE election_id = ?", (election_id,))
            result = cur.fetchone()
            if not result:
                return
            
            title, candidates_json = result
            candidates = json.loads(candidates_json) if candidates_json else []
            
            # Count votes per option
            cur.execute("""
                SELECT option_id, COUNT(*) as vote_count 
                FROM election_votes 
                WHERE election_id = ?
                GROUP BY option_id
                ORDER BY vote_count DESC
            """, (election_id,))
            
            vote_counts = cur.fetchall()
            
            # Determine winner
            winner_id = None
            winner_name = None
            max_votes = 0
            
            for option_id, vote_count in vote_counts:
                if vote_count > max_votes:
                    max_votes = vote_count
                    winner_id = option_id
                    for c in candidates:
                        if c.get('id') == option_id:
                            winner_name = c.get('name')
                            break
            
            # Generate OP_RETURN transaction (simplified - would be real tx in production)
            import hashlib
            import time
            op_return_data = f"ELECTION_RESULT:{election_id}:WINNER:{winner_id}:{winner_name}:VOTES:{max_votes}:TIME:{int(time.time())}"
            op_return_tx = hashlib.sha256(op_return_data.encode()).hexdigest()
            
            # Update election record
            cur.execute("""
                UPDATE elections 
                SET status = 'closed', 
                    result_winner = ?, 
                    result_sealed = 1,
                    op_return_tx = ?
                WHERE election_id = ?
            """, (winner_name, op_return_tx, election_id))
            
            conn.commit()
            
            print(f"[WINNER] Election '{title}' closed. Winner: {winner_name} with {max_votes} votes")
            print(f"[TX] OP_RETURN sealed: {op_return_tx[:16]}...")
            
            # Broadcast to WebSocket
            self.broadcast_result(election_id, winner_name, max_votes)
    
    def broadcast_result(self, election_id, winner, votes):
        """Broadcast election result to all connected clients"""
        try:
            from flask_socketio import emit
            from api import socketio
            
            socketio.emit('election_result', {
                'election_id': election_id,
                'winner': winner,
                'total_votes': votes,
                'timestamp': int(time.time())
            }, room='elections')
        except Exception as e:
            print(f"WebSocket broadcast failed: {e}")
    
    def run(self):
        """Main scheduler loop"""
        print("[VOTE] Election Scheduler started - checking every 3 seconds")
        while self.running:
            try:
                self.check_and_close_elections()
                time.sleep(3)  # Check every block (3 seconds)
            except Exception as e:
                print(f"Scheduler error: {e}")
    
    def start(self):
        """Start scheduler in background thread"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread

# Global instance
scheduler = None

def start_scheduler():
    global scheduler
    if scheduler is None:
        scheduler = ElectionScheduler()
        scheduler.start()
        print("[OK] Election scheduler started")
    return scheduler

if __name__ == "__main__":
    start_scheduler()
    while True:
        time.sleep(1)
