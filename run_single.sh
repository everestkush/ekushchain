#!/bin/bash
cd /home/kushal/everestkush
source venv/bin/activate

# Start miner in background with RocksDB write access
export IS_MINER=true
python3 fixed_miner.py &
MINER_PID=$!

# Wait for genesis block
sleep 5

# Start API in read-only mode
export IS_MINER=false
gunicorn -c gunicorn_config.py api:app

# Cleanup on exit
trap "kill $MINER_PID" EXIT
