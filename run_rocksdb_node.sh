#!/bin/bash
cd /home/kushal/everestkush
source venv/bin/activate
export EKUSH_STORAGE_BACKEND=rocksdb
export EKUSH_ROCKSDB_PATH=/home/kushal/everestkush/rocksdb_data
python3 -c "
from api import app
import threading
import time
from fixed_miner import start_miner

# Start miner in background thread
threading.Thread(target=start_miner, daemon=True).start()

# Start API
app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
"
