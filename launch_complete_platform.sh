#!/bin/bash
echo "=========================================="
echo "🚀 EverestKush Complete Platform Launch"
echo "=========================================="

# Activate virtual environment
source /home/kushal/everestkush/venv/bin/activate

# Upgrade database schema
echo "📦 Upgrading database schema..."
python3 /home/kushal/everestkush/upgrade_schema.py

# Launch Block Explorer (port 8082)
echo "🌐 Launching Block Explorer on port 8082..."
python3 /home/kushal/everestkush/block_explorer.py &
BLOCK_EXPLORER_PID=$!

# Launch WebSocket API (port 5001)
echo "🔌 Launching WebSocket API on port 5001..."
sudo systemctl start everestkush-websocket

# Launch Main API (port 5000)
echo "🏗️ Launching Main API on port 5000..."
sudo systemctl start everestkush-p2p

echo ""
echo "=========================================="
echo "✅ EVERESTKUSH PLATFORM READY!"
echo "=========================================="
echo "📍 Block Explorer: http://localhost:8082"
echo "📍 Main API: http://localhost:5000"
echo "📍 WebSocket API: ws://localhost:5001"
echo "📍 Health Check: http://localhost:5000/health"
echo ""
echo "Services running:"
echo "   - Blockchain Core"
echo "   - Smart Contracts (EVM-compatible)"
echo "   - DeFi Platform (Lending/Borrowing)"
echo "   - PoS Validators"
echo "   - Governance DAO"
echo "   - NFT Marketplace"
echo "   - Cross-chain Bridges"
echo "   - Price Oracle"
echo ""
echo "Press Ctrl+C to stop block explorer only"
echo "=========================================="

# Keep script running
wait $BLOCK_EXPLORER_PID
