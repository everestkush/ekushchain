bind = "0.0.0.0:5000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 5
max_requests = 10000
max_requests_jitter = 1000
graceful_timeout = 10
accesslog = "/var/log/ekush/access.log"
errorlog = "/var/log/ekush/error.log"
loglevel = "info"

# RocksDB - API workers use read-only mode
import os
os.environ['EKUSH_READ_ONLY'] = 'true'

# Environment for read-only RocksDB access
import os
os.environ['IS_MINER'] = 'false'
