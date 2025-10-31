#!/bin/bash
set -e

# Purpose: Test Microservice Monitoring project components
# Usage: Run in WSL2 Ubuntu terminal after running 'make port-forward-all'

echo "Testing microservices..."
kubectl get pods -n default
kubectl get svc -n default

echo ""
echo "Running load test against frontend..."
echo "Note: Make sure port-forward-all is running first"

# Check if frontend is accessible via port forward
if curl -s http://localhost:5000 >/dev/null 2>&1; then
    echo "✓ Frontend is accessible via localhost:5000"

    # Run simple load test
    echo "Generating 10 requests..."
    for i in {1..10}; do
        curl -s http://localhost:5000 >/dev/null && echo "  Request $i: Success" || echo "  Request $i: Failed"
        sleep 0.5
    done

    echo ""
    echo "✓ Load test completed!"
    echo ""
    echo "Check metrics in:"
    echo "  - Grafana:    http://localhost:3000"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Jaeger:     http://localhost:16686"
else
    echo "✗ Frontend not accessible on localhost:5000"
    echo ""
    echo "Please run: make port-forward-all"
    echo "Then try again: make test"
    exit 1
fi