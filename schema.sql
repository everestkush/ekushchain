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
);

CREATE TABLE IF NOT EXISTS transactions (
    tx_hash TEXT PRIMARY KEY,
    block_idx INTEGER,
    sender TEXT NOT NULL,
    recipient TEXT NOT NULL,
    amount REAL NOT NULL,
    fee REAL NOT NULL,
    timestamp REAL NOT NULL,
    signature TEXT,
    FOREIGN KEY (block_idx) REFERENCES blocks(idx)
);

CREATE TABLE IF NOT EXISTS pending_transactions (
    tx_hash TEXT PRIMARY KEY,
    sender TEXT NOT NULL,
    recipient TEXT NOT NULL,
    amount REAL NOT NULL,
    fee REAL NOT NULL,
    timestamp REAL NOT NULL,
    signature TEXT
);

CREATE TABLE IF NOT EXISTS balances (
    address TEXT PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    updated_at INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS validators (
    address TEXT PRIMARY KEY,
    bonded_amount INTEGER,
    status TEXT DEFAULT 'pending',
    joined_at INTEGER,
    last_active INTEGER,
    slashed_amount INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS mining_rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_height INTEGER UNIQUE,
    validator_address TEXT NOT NULL,
    reward_amount INTEGER NOT NULL,
    fees_collected INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s','now'))
);

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
);

INSERT OR IGNORE INTO allocation_wallets (id, name, amount, percentage, multisig_required, vesting_days, cliff_days, created_at, status)
VALUES 
('public', 'Public Allocation', 300000000, 30, 1, 0, 0, strftime('%s','now'), 'active'),
('validator', 'Validator Rewards', 300000000, 30, 5, 0, 0, strftime('%s','now'), 'active'),
('development', 'Development Fund', 150000000, 15, 5, 563, 0, strftime('%s','now'), 'active'),
('ecosystem', 'Ecosystem Fund', 150000000, 15, 5, 928, 0, strftime('%s','now'), 'active'),
('crisis', 'Crisis Reserve', 100000000, 10, 15, 2761, 0, strftime('%s','now'), 'active');
