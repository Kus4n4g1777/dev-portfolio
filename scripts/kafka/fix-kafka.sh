#!/bin/bash
# ===================================================================
# Kafka Container Fix & Restart Script
# ===================================================================
# Purpose: Fix common Kafka startup issues and restart in correct order
# Location: scripts/kafka/fix-kafka.sh
# Usage: ./scripts/kafka/fix-kafka.sh
# ===================================================================

set -e  # Exit on error

echo "🔧 === Kafka Fix & Restart Script ==="
echo ""

# Step 1: Stop all containers gracefully
echo "📦 Stopping all containers..."
docker-compose down
echo "✅ All containers stopped"
echo ""

# Step 2: Remove Kafka volumes (fixes most corruption issues)
echo "🗑️  Removing Kafka volumes..."
docker volume rm dev-portfolio_kafka_data 2>/dev/null && echo "✅ Kafka volumes removed" || echo "ℹ️  No Kafka volumes to remove"
echo ""

# Step 3: Clean up any orphaned Kafka data
echo "🧹 Cleaning orphaned data..."
docker volume prune -f
echo "✅ Cleanup complete"
echo ""

# Step 4: Start Zookeeper first (Kafka depends on it)
echo "🚀 Starting Zookeeper..."
docker-compose up -d zookeeper

echo "⏳ Waiting for Zookeeper to be healthy (30 seconds)..."
for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""
echo "✅ Zookeeper should be ready"
echo ""

# Step 5: Verify Zookeeper is actually healthy
echo "🔍 Verifying Zookeeper health..."
if docker-compose ps zookeeper | grep -q "healthy"; then
    echo "✅ Zookeeper is healthy"
else
    echo "⚠️  Warning: Zookeeper might not be fully healthy yet"
fi
echo ""

# Step 6: Start Kafka
echo "🚀 Starting Kafka..."
docker-compose up -d kafka

echo "⏳ Waiting for Kafka to stabilize (20 seconds)..."
for i in {1..20}; do
    echo -n "."
    sleep 1
done
echo ""
echo "✅ Kafka should be ready"
echo ""

# Step 7: Start remaining services
echo "🚀 Starting remaining services..."
docker-compose up -d

echo "⏳ Giving all services time to initialize (10 seconds)..."
sleep 10
echo ""

# Step 8: Show status
echo "📊 === Container Status ==="
docker-compose ps
echo ""

# Step 9: Quick health check
echo "🏥 === Quick Health Checks ==="
echo ""
echo "Zookeeper:"
docker-compose ps zookeeper | tail -n +2
echo ""
echo "Kafka:"
docker-compose ps kafka | tail -n +2
echo ""

# Step 10: Offer to show logs
echo "✅ === Restart Complete! ==="
echo ""
echo "📝 Next steps:"
echo "  - View Kafka logs: docker logs kafka"
echo "  - View Zookeeper logs: docker logs zookeeper"
echo "  - Check all logs: docker-compose logs -f"
echo "  - Test Kafka: docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list"
echo ""
echo "🎯 Common issues:"
echo "  - If Kafka still fails: Check docker-compose.yml for KAFKA_ADVERTISED_LISTENERS"
echo "  - If Zookeeper fails: Check port 2181 is not in use"
echo "  - Disk space: docker system df"
echo ""