#!/bin/bash
cd /home/kushal/everestkush
source venv/bin/activate

# Create test transactions
sqlite3 ekush_chain.db "DELETE FROM pending_transactions;"
for i in 1 2 3 4 5; do
sqlite3 ekush_chain.db "INSERT INTO pending_transactions (tx_hash, sender, recipient, amount, fee, timestamp, signature) VALUES (hex(randomblob(32)), 'user1', 'user2', 10, 0.1, strftime('%s','now'), 'sig');"
done

# Start API in background
nohup gunicorn --bind 0.0.0.0:5000 --workers 1 api:app > api.log 2>&1 &
echo "API started"

# Start miner in background
nohup python3 -c "
import sys, time, sqlite3
sys.path.insert(0, '.')
from core.block import EKUSHChain
from core.transaction import EKUSHTransaction

# Get validator
conn = sqlite3.connect('ekush_chain.db')
cur = conn.execute('SELECT address FROM validators WHERE status=\"active\" LIMIT 1')
val = cur.fetchone()
conn.close()

if not val:
    print('No validator')
    exit(1)

validator = val[0]
print(f'Mining with {validator[:20]}...')

while True:
    try:
        bc = EKUSHChain()
        conn = sqlite3.connect('ekush_chain.db')
        rows = conn.execute('SELECT tx_hash, sender, recipient, amount, fee, timestamp, signature FROM pending_transactions').fetchall()
        conn.close()
        
        for row in rows:
            tx = EKUSHTransaction(sender=row[1], recipient=row[2], amount=row[3], fee=row[4])
            tx.txid = row[0]
            tx.timestamp = row[5]
            tx.signature = row[6] if row[6] else b''
            bc.pending_transactions.append(tx)
        
        block = bc.add_block(validator)
        if block:
            print(f'Block {block.index} mined with {len(block.transactions)} txs')
            conn = sqlite3.connect('ekush_chain.db')
            for tx in block.transactions:
                conn.execute('DELETE FROM pending_transactions WHERE tx_hash = ?', (tx.txid,))
            conn.commit()
            conn.close()
        time.sleep(3)
    except Exception as e:
        print(f'Error: {e}')
        time.sleep(3)
" > miner.log 2>&1 &

echo "Miner started"
echo "Check: curl http://localhost:5000/stats"
