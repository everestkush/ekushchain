"""
Centralized database initialization for EverestKush
Each node runs this independently -- no central server
"""
import sqlite3
import os
import time

DB_PATH = "/home/kushal/everestkush/ekush_chain.db"

def init_all_tables():
    """Initialize all database tables -- runs on every node locally"""
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA synchronous=NORMAL")
    cur = conn.cursor()
    
    # Blocks table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            idx INTEGER PRIMARY KEY,
            hash TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            validator TEXT NOT NULL,
            timestamp REAL NOT NULL,
            nonce INTEGER DEFAULT 0,
            merkle_root TEXT NOT NULL,
            reward INTEGER DEFAULT 0,
            transactions_count INTEGER DEFAULT 0
        )
    ''')
    
    # Transactions table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            tx_hash TEXT PRIMARY KEY,
            block_idx INTEGER,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            amount REAL NOT NULL,
            fee REAL NOT NULL,
            timestamp REAL NOT NULL,
            signature TEXT,
            public_key TEXT,
            FOREIGN KEY (block_idx) REFERENCES blocks(idx)
        )
    ''')
    
    # Pending transactions
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pending_transactions (
            tx_hash TEXT PRIMARY KEY,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            amount REAL NOT NULL,
            fee REAL NOT NULL,
            timestamp REAL NOT NULL,
            signature TEXT,
            public_key TEXT
        )
    ''')
    
    # Mempool table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS mempool (
            tx_hash TEXT PRIMARY KEY,
            transaction_data TEXT,
            fee_per_byte REAL,
            timestamp INTEGER
        )
    ''')
    
    # UTXOs table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS utxos (
            outpoint TEXT PRIMARY KEY,
            address TEXT,
            amount INTEGER,
            script_pubkey TEXT,
            block_height INTEGER,
            is_spent INTEGER DEFAULT 0,
            is_frozen INTEGER DEFAULT 0,
            created_at INTEGER,
            spent_at INTEGER
        )
    ''')
    
    # Balances table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            address TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            updated_at INTEGER DEFAULT 0
        )
    ''')
    
    # Validators table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS validators (
            address TEXT PRIMARY KEY,
            bonded_amount INTEGER,
            status TEXT DEFAULT 'pending',
            joined_at INTEGER,
            last_active INTEGER,
            slashed_amount INTEGER DEFAULT 0
        )
    ''')
    
    # Mining rewards table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS mining_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_height INTEGER UNIQUE,
            validator_address TEXT NOT NULL,
            reward_amount INTEGER NOT NULL,
            fees_collected INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )
    ''')
    
    # Allocation wallets table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS allocation_wallets (
            id TEXT PRIMARY KEY,
            name TEXT,
            address TEXT,
            amount INTEGER,
            percentage INTEGER,
            multisig_required INTEGER,
            vesting_days INTEGER,
            cliff_days INTEGER,
            released_amount INTEGER DEFAULT 0,
            created_at INTEGER,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Voters table (no private keys)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS voters (
            voter_id TEXT PRIMARY KEY,
            public_key TEXT,
            wallet_address TEXT,
            has_voted INTEGER DEFAULT 0,
            vote_commitment TEXT,
            vote_tx TEXT,
            created_at INTEGER
        )
    ''')
    
    # Wallets table (no private keys)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            address TEXT PRIMARY KEY,
            public_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Nonces table (for replay protection)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS nonces (
            private_key TEXT,
            nonce INTEGER,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(private_key, nonce)
        )
    ''')
    
    # Governance tables
    cur.execute('''
        CREATE TABLE IF NOT EXISTS governance_proposals (
            proposal_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            proposal_type TEXT,
            proposer TEXT,
            status TEXT DEFAULT 'active',
            yes_votes REAL DEFAULT 0,
            no_votes REAL DEFAULT 0,
            abstain_votes REAL DEFAULT 0,
            total_voting_power REAL DEFAULT 0,
            created_at INTEGER,
            end_time INTEGER
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS governance_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id TEXT,
            voter TEXT,
            choice TEXT,
            voting_power REAL,
            timestamp INTEGER,
            FOREIGN KEY (proposal_id) REFERENCES governance_proposals(proposal_id)
        )
    ''')
    
    # Elections table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS elections (
            election_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            creator TEXT,
            options TEXT,
            tier TEXT DEFAULT 'community',
            fee_paid INTEGER,
            voter_limit INTEGER,
            option_limit INTEGER,
            duration_days INTEGER,
            start_time INTEGER,
            end_time INTEGER,
            status TEXT DEFAULT 'active',
            created_at INTEGER
        )
    ''')
    
    # Indices for performance
    cur.execute("CREATE INDEX IF NOT EXISTS idx_utxos_address ON utxos(address)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_utxos_is_spent ON utxos(is_spent)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_blocks_height ON blocks(idx)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_validators_status ON validators(status)")
    
    conn.commit()
    conn.close()
    print("[OK] Database tables initialized")

def init_allocation_wallets():
    """Insert allocation wallets -- same on every node"""
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA synchronous=NORMAL")
    cur = conn.cursor()
    
    allocations = [
        ('public', 'Public Allocation', 300000000, 30, 1, 0, 0),
        ('validator', 'Validator Rewards', 300000000, 30, 5, 0, 0),
        ('development', 'Development Fund', 150000000, 15, 5, 563, 0),
        ('ecosystem', 'Ecosystem Fund', 150000000, 15, 5, 928, 0),
        ('crisis', 'Crisis Reserve', 100000000, 10, 15, 2761, 0),
    ]
    
    for aid, name, amount, pct, multisig, vesting, cliff in allocations:
        cur.execute('''
            INSERT OR IGNORE INTO allocation_wallets 
            (id, name, amount, percentage, multisig_required, vesting_days, cliff_days, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (aid, name, amount, pct, multisig, vesting, cliff, int(time.time()), 'active'))
    
    conn.commit()
    conn.close()
    print("[OK] Allocation wallets initialized")

def init_genesis_block():
    """Initialize genesis block if chain is empty"""
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA synchronous=NORMAL")
    cur = conn.cursor()
    
    # Check if any blocks exist
    cur.execute("SELECT COUNT(*) FROM blocks")
    count = cur.fetchone()[0]
    
    if count == 0:
        # Create genesis block
        genesis_hash = "0" * 64
        cur.execute('''
            INSERT INTO blocks (idx, hash, previous_hash, validator, timestamp, merkle_root)
            VALUES (0, ?, ?, 'genesis', ?, '0'*64)
        ''', (genesis_hash, genesis_hash, int(time.time())))
        conn.commit()
        print("[OK] Genesis block created")
    
    conn.close()

def ensure_initialized():
    """Run all initialization functions -- called on every node startup"""
    init_all_tables()
    init_allocation_wallets()
    init_genesis_block()
    print("[START] Database ready")

if __name__ == "__main__":
    ensure_initialized()
