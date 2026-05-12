#!/bin/bash
# EverestKush Full Node Startup Script with all enterprise features

export EVERESTKUSH_HOME="$(cd "$(dirname "$0")" && pwd)"
cd $EVERESTKUSH_HOME

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export FLASK_APP=api.py
export FLASK_ENV=production
export EVERESTKUSH_REGTEST=${EVERESTKUSH_REGTEST:-false}
export EVERESTKUSH_PRUNE=${EVERESTKUSH_PRUNE:-0}
export EVERESTKUSH_ZMQ_PORT=${EVERESTKUSH_ZMQ_PORT:-28332}
export EVERESTKUSH_ELECTRUM_PORT=${EVERESTKUSH_ELECTRUM_PORT:-50001}

echo "🚀 Starting EverestKush Node with enterprise features..."
echo "   - Reorg recovery: enabled"
echo "   - AssumeUTXO: ready"
echo "   - Pruning: ${EVERESTKUSH_PRUNE:-disabled}"
echo "   - ZMQ streaming: port ${EVERESTKUSH_ZMQ_PORT}"
echo "   - Electrum protocol: port ${EVERESTKUSH_ELECTRUM_PORT}"
echo "   - Prometheus metrics: /metrics"
echo "   - Health checks: /health"
echo "   - JSON-RPC: /rpc/json-rpc"

# Start the node
exec gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --capture-output \
    api:app
