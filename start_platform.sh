#!/bin/bash
set -e

echo "============================================================"
echo "   [STARTUP] Starting Real-Time Conversational Platform    "
echo "============================================================"

# 1. Enable Swap space if not already active
if ! swapon --show | grep -q "/swapfile"; then
    if [ -f /swapfile ]; then
        sudo swapon /swapfile || true
        echo "✅ [SWAP] Enabled 4GB Swap file."
    fi
else
    echo "✅ [SWAP] 4GB Swap file is active."
fi

# 2. Start Docker Containers
echo "[DOCKER] Starting MongoDB, Neo4j, and Kafka containers..."
sudo systemctl start docker || true
sudo docker start mongodb neo4j kafka || true
echo "✅ [DOCKER] Containers running:"
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 3. Start PM2 Streaming Services
echo "[PM2] Resurrecting background streaming processes..."
cd ~/Real-Time-Conversational-Intelligence-Platform
pm2 start ecosystem.config.js || pm2 resurrect || true
pm2 status

PUBLIC_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')

echo "============================================================"
echo "   🚀 [READY FOR INTERVIEW / DEMO] Platform Online!"
echo "   Server Public IP: $PUBLIC_IP"
echo "   Neo4j Bolt URI: bolt://$PUBLIC_IP:7687"
echo "============================================================"
