"""Prometheus metrics endpoint for monitoring"""
from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
from flask import Response
import time
import os

# Define metrics
BLOCK_HEIGHT = Gauge('everestkush_block_height', 'Current blockchain height')
MEMPOOL_SIZE = Gauge('everestkush_mempool_tx_count', 'Number of transactions in mempool')
PEER_COUNT = Gauge('everestkush_connected_peers', 'Number of connected peers')
BLOCK_PROPAGATION = Histogram('everestkush_block_propagation_seconds', 'Block propagation delay')
REORG_COUNT = Counter('everestkush_reorg_total', 'Number of chain reorganizations')
DB_SIZE = Gauge('everestkush_db_size_bytes', 'Database file size')
TX_RATE = Counter('everestkush_transactions_total', 'Total transactions processed')
BLOCK_TIME = Histogram('everestkush_block_interval_seconds', 'Time between blocks')

def update_metrics(chain_height=None, mempool_tx_count=None, peer_count=None):
    """Update all metrics with current values"""
    if chain_height is not None:
        BLOCK_HEIGHT.set(chain_height)
    
    if mempool_tx_count is not None:
        MEMPOOL_SIZE.set(mempool_tx_count)
    
    if peer_count is not None:
        PEER_COUNT.set(peer_count)
    
    # Update DB size
    if os.path.exists(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")):
        DB_SIZE.set(os.path.getsize(os.environ.get("EKUSH_DB_PATH", "/home/kushal/everestkush/ekush_chain.db")))

def metrics_endpoint():
    """Flask endpoint: /metrics"""
    return Response(generate_latest(REGISTRY), mimetype='text/plain')

def record_reorg():
    """Record a chain reorganization event"""
    REORG_COUNT.inc()

def record_transaction():
    """Record a new transaction"""
    TX_RATE.inc()

def record_block_time(seconds):
    """Record time since last block"""
    BLOCK_TIME.observe(seconds)
