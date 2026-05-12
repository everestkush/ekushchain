#!/bin/bash
# EverestKush Node Installer - Full Node
# Run: curl -sL http://103.74.15.88:5000/install_node.sh | bash

set -e
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🚀 EverestKush Node Installer"
echo "================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3.9+ required${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python found${NC}"

# Create directory
mkdir -p ~/ekush-node
cd ~/ekush-node

# Download full node code from main server
echo "📥 Downloading EverestKush node..."
curl -sL http://103.74.15.88:5000/static/node_full.tar.gz -o node_full.tar.gz 2>/dev/null || {
    echo "⚠️ Downloading individual files..."
    
    # Download essential files
    for file in run_node.py api.py core network requirements.txt; do
        curl -sL "http://103.74.15.88:5000/static/$file" -o "$file" 2>/dev/null || echo "  Skipping $file"
    done
}

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask flask-cors flask-socketio requests gunicorn

# Create seed config
cat > seeds.json << SEEDS
{
    "seed_nodes": ["103.74.15.88:8333", "192.168.23.5:8333"],
    "p2p_port": 8333,
    "api_port": 5000
}
SEEDS

# Create systemd service (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo tee /etc/systemd/system/ekush-node.service << SRV
[Unit]
Description=EverestKush Full Node
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/ekush-node
ExecStart=$HOME/ekush-node/venv/bin/python3 $HOME/ekush-node/run_node.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SRV
    sudo systemctl daemon-reload
    sudo systemctl enable ekush-node
    sudo systemctl start ekush-node
    echo -e "${GREEN}✅ Node service started${NC}"
else
    echo "Run manually: cd ~/ekush-node && source venv/bin/activate && python3 run_node.py"
fi

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "📡 Node will sync from seed nodes: 103.74.15.88:8333"
echo "🔍 Check status: curl http://localhost:5000/stats"
echo "💰 To become validator: need 8,888 EKUSH bonded"
