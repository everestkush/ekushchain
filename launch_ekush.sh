#!/bin/bash
cd /home/kushal/everestkush
source venv/bin/activate

# Start P2P gossip
nohup python3 -c "
from network.p2p_gossip import p2p_gossip
p2p_gossip.start()
import time
while True:
    time.sleep(60)
" > /tmp/p2p_gossip.log 2>&1 &

# Start API with gunicorn (production)
nohup gunicorn -c gunicorn_config.py api:app > api.log 2>&1 &

# Start miner
nohup python3 fixed_miner.py > miner.log 2>&1 &

echo "API and Miner started with gunicorn"
