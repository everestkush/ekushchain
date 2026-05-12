#!/bin/bash
# Start EverestKush in Regtest mode - Better than Bitcoin!

echo "🔥 Starting EverestKush REGTEST MODE"
echo "====================================="
echo "⚡ Instant block mining (2 seconds)"
echo "💰 Pre-funded wallets ready"
echo "🎮 No peers needed"
echo "====================================="

# Set regtest environment
export EVERESTKUSH_REGTEST=true
export FLASK_APP=api.py

# Start the node
source venv/bin/activate
python api.py
