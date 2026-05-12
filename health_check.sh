#!/bin/bash
# EverestKush Complete Health Check

API_URL="http://localhost:5000"
source /home/kushal/everestkush/.env 2>/dev/null

echo "=========================================="
echo "🏔️ EverestKush Health Check"
echo "=========================================="
echo "Time: $(date)"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check function
check() {
    local name=$1
    local status=$2
    if [ "$status" = "OK" ]; then
        echo -e "  ${GREEN}✅ $name${NC}"
    else
        echo -e "  ${RED}❌ $name - $status${NC}"
    fi
}

# 1. Service Status
echo "1. Service Status:"
if systemctl is-active --quiet everestkush-p2p; then
    check "Main API" "OK"
else
    check "Main API" "Not running"
fi

# 2. Endpoint Tests
echo -e "\n2. Endpoint Tests:"

# Health endpoint
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
if [ "$HEALTH" = "200" ]; then
    check "Health Endpoint" "OK"
else
    check "Health Endpoint" "HTTP $HEALTH"
fi

# Stats endpoint
STATS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/stats")
if [ "$STATS" = "200" ]; then
    check "Stats Endpoint" "OK"
    # Get actual stats
    BLOCK=$(curl -s "$API_URL/api/stats" | python3 -c "import sys,json; print(json.load(sys.stdin).get('block_height', 'N/A'))" 2>/dev/null)
    TX=$(curl -s "$API_URL/api/stats" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_transactions', 'N/A'))" 2>/dev/null)
    echo "     Block Height: $BLOCK"
    echo "     Total TX: $TX"
else
    check "Stats Endpoint" "HTTP $STATS"
fi

# Balance endpoint
BALANCE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/balance/ekush1public00000000000000000000")
if [ "$BALANCE" = "200" ]; then
    check "Balance Endpoint" "OK"
    # Get actual balance
    BAL=$(curl -s "$API_URL/balance/ekush1public00000000000000000000" | python3 -c "import sys,json; print(f\"{json.load(sys.stdin).get('balance_ekush', 0):.2f} EKUSH\")" 2>/dev/null)
    echo "     Balance: $BAL"
else
    check "Balance Endpoint" "HTTP $BALANCE"
fi

# 3. Security Tests
echo -e "\n3. Security Tests:"

# API Key protection
NO_KEY=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/rpc/getwork")
if [ "$NO_KEY" = "401" ]; then
    check "API Key Protection" "OK (401 without key)"
else
    check "API Key Protection" "Returned $NO_KEY"
fi

# With valid key
if [ ! -z "$API_KEY" ]; then
    WITH_KEY=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/rpc/getwork" \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" -d '{}')
    if [ "$WITH_KEY" = "200" ]; then
        check "API Key Auth" "OK (200 with key)"
    else
        check "API Key Auth" "Returned $WITH_KEY"
    fi
fi

# 4. WebSocket Status
echo -e "\n4. WebSocket Status:"
WS=$(curl -s "http://localhost:5000/socket.io/?EIO=4&transport=polling" | head -c 50)
if [[ "$WS" == *"sid"* ]]; then
    echo "  ✅ WebSocket handshake successful"
else
    echo "  ⚠️ WebSocket: ${WS}..."
fi

# 5. Block Explorer
echo -e "\n5. Block Explorer:"
EXP=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8082/" 2>/dev/null)
if [ "$EXP" = "200" ]; then
    echo "  ✅ Block Explorer running on port 8082"
else
    echo "  ⚠️ Block Explorer: HTTP $EXP"
fi

echo -e "\n=========================================="
echo "✅ Health check complete!"
echo "=========================================="
