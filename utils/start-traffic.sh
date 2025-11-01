#!/bin/bash

echo "🚀 Starting Traffic Simulation for Metrics Generation"
echo "========================================================"

# Get content service URL
CONTENT_URL=$(minikube service content-service -n default --url 2>/dev/null)

if [ -z "$CONTENT_URL" ]; then
    echo "❌ Error: Could not get content-service URL"
    echo "Make sure minikube is running and content-service is deployed"
    exit 1
fi

echo "📍 Content Service URL: $CONTENT_URL"

# Start simulation
echo ""
echo "▶️  Starting traffic simulation..."
RESPONSE=$(curl -s -X POST "$CONTENT_URL/api/simulation/start")
echo "Response: $RESPONSE"

# Check status
echo ""
echo "📊 Simulation Status:"
curl -s "$CONTENT_URL/api/simulation/status" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"  Status: {data.get('status')}\n  Running: {data.get('simulation_running')}\")" 2>/dev/null || echo "  $RESPONSE"

# Generate some initial traffic
echo ""
echo "🔄 Generating initial traffic (creating creators and content)..."
for i in {1..5}; do
    curl -s -X POST "$CONTENT_URL/api/creators" -H "Content-Type: application/json" -d '{"name":"LoadTest Creator"}' > /dev/null
    echo "  ✓ Created creator $i"
done

echo ""
echo "✅ Traffic simulation started!"
echo ""
echo "📈 Next steps:"
echo "  1. Wait 2-3 minutes for metrics to accumulate"
echo "  2. In Grafana, refresh the dashboard"
echo "  3. Check Prometheus: minikube service prometheus-operator-kube-p-prometheus -n monitoring --url"
echo ""
echo "🛑 To stop simulation:"
echo "  curl -X POST $CONTENT_URL/api/simulation/stop"
