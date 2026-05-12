#!/bin/bash
echo "=== EverestKush Node Starting ==="

if [ ! -f /data/ekush_chain.db ]; then
    echo "Fresh node -- initializing DB..."
    sqlite3 /data/ekush_chain.db < /app/schema.sql
fi

echo "Syncing chain from peers..."
EKUSH_DB_PATH=/data/ekush_chain.db python3 /app/node_sync.py

echo "Starting API and miner..."
EKUSH_DB_PATH=/data/ekush_chain.db python3 -c \
    "from api import app; app.run(host='0.0.0.0', port=5000)" &
EKUSH_DB_PATH=/data/ekush_chain.db python3 fixed_miner.py
