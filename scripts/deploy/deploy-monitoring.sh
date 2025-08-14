#!/bin/bash

# This script deploys the monitoring stack and optionally sets up port-forwarding.

set -e # Exit immediately if a command exits with a non-zero status.

echo "🚀 Deploying Monitoring Stack..."
kubectl apply -f Nexus-cursor/iac/kubernetes/monitoring/
echo "✅ Monitoring stack deployment initiated."
echo

# Prompt user to check pod status
read -p "Do you want to watch the pod status now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl get pods -n nexus-platform -w
fi

echo

# --- NEW: Prompt user to start port-forwarding ---
read -p "Do you want to start port-forwarding for all services? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting port-forwarding in the background..."

    # Kill any previous port-forwards to prevent errors
    pkill -f "kubectl port-forward" || true

    # Start new port-forwards as background jobs
    kubectl port-forward svc/grafana-service 3000:3000 -n nexus-platform &
    kubectl port-forward svc/prometheus-service 9090:9090 -n nexus-platform &
    kubectl port-forward svc/alertmanager-service 9093:9093 -n nexus-platform &

    GREEN='\033[0;32m'
    NC='\033[0m' # No Color

    echo -e "${GREEN}Services are now accessible at:${NC}"
    echo "  - Grafana:       http://localhost:3000"
    echo "  - Prometheus:    http://localhost:9090"
    echo "  - Alertmanager:  http://localhost:9093"
    echo
    echo "NOTE: Port-forwarding is running in the background."
    echo "To stop it later, run the command: pkill -f \"kubectl port-forward\""
fi
