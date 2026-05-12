FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    curl \
    sqlite3 \
    librocksdb-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install rocksdict

COPY . .

RUN echo '#!/bin/bash\n\
# Start P2P gossip\n\
python3 -c "\n\
from network.p2p_gossip import p2p_gossip\n\
p2p_gossip.start()\n\
import time\n\
while True:\n\
    time.sleep(60)\n\
" > /tmp/p2p_gossip.log 2>&1 &\n\
\n\
# Start miner\n\
python3 miner_rocksdb_final.py &\n\
\n\
# Start API\n\
export EKUSH_STORAGE_BACKEND=rocksdb\n\
export EKUSH_ROCKSDB_PATH=/data/rocksdb_data\n\
export EKUSH_READ_ONLY=true\n\
gunicorn -c gunicorn_config.py api:app\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 5000 8333 8334

VOLUME ["/data"]

ENTRYPOINT ["/entrypoint.sh"]
